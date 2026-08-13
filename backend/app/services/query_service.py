import time
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.database import ChatSessionModel, ChatMessageModel
from app.retrieval.query_analyzer import QueryAnalyzer, AnalyzedQuery
from app.retrieval.retriever import HybridRetriever
from app.ranking.reranker import Reranker
from app.ranking.deduplicator import Deduplicator
from app.context.context_engine import ContextEngine
from app.llm.factory import LLMFactory
from app.core.config import settings
from app.core.logging import logger


SYSTEM_RAG_INSTRUCTION = """You are Load2Ask, an expert RAG Assistant.
Your task is to answer the user's question accurately, clearly, and objectively based STRICTLY on the provided retrieved context.

RULES:
1. Base your answer ONLY on the provided retrieved knowledge context.
2. Always cite your sources in the text using [Source 1], [Source 2], etc.
3. If the context does not contain sufficient information to answer the question, state EXACTLY:
"I could not find sufficient information in the provided sources to answer this reliably."
4. Do NOT hallucinate, assume, or invent facts outside the retrieved sources.
"""


class RAGQueryService:
    """End-to-end Multimodal RAG Query and Conversational Service with Observability and Configurable Parameters."""

    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.reranker = Reranker(top_k=settings.RERANK_TOP_K)
        self.context_engine = ContextEngine(context_budget_tokens=settings.CONTEXT_TOKEN_LIMIT)
        self.llm = LLMFactory.get_llm()

    def _get_or_create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> ChatSessionModel:
        if session_id:
            session = self.db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
            if session:
                return session

        new_session = ChatSessionModel(
            id=session_id or str(uuid.uuid4()),
            title=title or "RAG Chat Session"
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

    def _get_history_messages(self, session_id: str) -> List[Dict[str, str]]:
        messages = (
            self.db.query(ChatMessageModel)
            .filter(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        filter_doc_id: Optional[str] = None,
        top_k: Optional[int] = None,
        rerank_k: Optional[int] = None,
        context_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline with observability timing:
        Query -> Conversation Resolution -> Analysis -> Hybrid Retrieval -> Reranking -> Deduplication -> Context Engine -> LLM -> Citations.
        """
        t0 = time.perf_counter()

        # Configurable Parameters
        retrieval_k = top_k or settings.RETRIEVAL_TOP_K
        rerank_top_k = rerank_k or settings.RERANK_TOP_K
        token_budget = context_budget or settings.CONTEXT_TOKEN_LIMIT

        # 1. Chat Session & History
        session = self._get_or_create_session(session_id, title=query[:30])
        history = self._get_history_messages(session.id)

        # 2. Query Understanding & Conversational Resolution
        analyzed_query: AnalyzedQuery = QueryAnalyzer.analyze(query, conversation_history=history)

        # 3. Hybrid Retrieval (Dense Vector + BM25 Lexical)
        t_ret_start = time.perf_counter()
        raw_candidates = self.retriever.retrieve(
            analyzed_query=analyzed_query,
            top_k=retrieval_k,
            alpha=settings.DENSE_WEIGHT,
            beta=settings.LEXICAL_WEIGHT,
            filter_doc_id=filter_doc_id
        )
        t_ret_end = time.perf_counter()
        retrieval_latency_ms = round((t_ret_end - t_ret_start) * 1000, 2)

        # 4. Re-ranking
        t_rerank_start = time.perf_counter()
        reranked_candidates = self.reranker.rerank(raw_candidates, analyzed_query=analyzed_query, top_k=rerank_top_k)
        t_rerank_end = time.perf_counter()
        reranking_latency_ms = round((t_rerank_end - t_rerank_start) * 1000, 2)

        # 5. Deduplication & Relevance Thresholding
        deduped_candidates = Deduplicator.deduplicate(reranked_candidates, similarity_threshold=settings.DEDUPLICATION_THRESHOLD)
        relevant_candidates = [(chunk, score) for chunk, score in deduped_candidates if score >= settings.RELEVANCE_THRESHOLD]

        # 6. Context Engine (Lost-in-the-middle ordering + Token budgeting + Formatting)
        t_ctx_start = time.perf_counter()
        context_str, selected_chunks, citations, token_count = self.context_engine.build_context(
            relevant_candidates,
            token_budget=token_budget
        )
        t_ctx_end = time.perf_counter()
        context_latency_ms = round((t_ctx_end - t_ctx_start) * 1000, 2)

        # 7. LLM Generation
        t_llm_start = time.perf_counter()
        if not context_str.strip():
            answer = "I could not find sufficient information in the provided sources to answer this reliably."
        else:
            prompt = f"Retrieved Context:\n{context_str}\n\nUser Query: {analyzed_query.rewritten_query}"
            answer = self.llm.generate(
                prompt=prompt,
                system_instruction=SYSTEM_RAG_INSTRUCTION,
                temperature=0.2
            )
        t_llm_end = time.perf_counter()
        llm_latency_ms = round((t_llm_end - t_llm_start) * 1000, 2)
        total_latency_ms = round((t_llm_end - t0) * 1000, 2)

        # 8. Store Chat Messages in SQL DB
        user_msg = ChatMessageModel(
            session_id=session.id,
            role="user",
            content=query
        )
        assistant_msg = ChatMessageModel(
            session_id=session.id,
            role="assistant",
            content=answer,
            msg_metadata={"sources": citations}
        )

        self.db.add_all([user_msg, assistant_msg])
        self.db.commit()

        # 9. Structured Observability Logging
        source_ids = list({c.get("document_id") for c in citations if c.get("document_id")})
        observability_data = {
            "session_id": session.id,
            "query": query,
            "rewritten_query": analyzed_query.rewritten_query,
            "retrieval_latency_ms": retrieval_latency_ms,
            "reranking_latency_ms": reranking_latency_ms,
            "context_engine_latency_ms": context_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "total_latency_ms": total_latency_ms,
            "retrieved_candidates_count": len(raw_candidates),
            "reranked_candidates_count": len(reranked_candidates),
            "selected_context_count": len(selected_chunks),
            "retrieved_chunk_count": len(raw_candidates),
            "reranked_chunk_count": len(reranked_candidates),
            "selected_chunk_count": len(selected_chunks),
            "context_token_count": token_count,
            "token_usage": {
                "context_tokens": token_count,
                "answer_tokens": self.context_engine.count_tokens(answer)
            },
            "source_ids": source_ids
        }

        logger.log_observability("rag_query_execution", observability_data)

        # 10. Debug metadata payload for frontend / client response
        debug_info = {
            **observability_data,
            "original_query": analyzed_query.original_query,
            "expanded_queries": analyzed_query.expanded_queries,
            "intent": analyzed_query.intent,
            "extracted_keywords": analyzed_query.keywords,
        }


        return {
            "session_id": session.id,
            "query": query,
            "rewritten_query": analyzed_query.rewritten_query,
            "answer": answer,
            "sources": citations,
            "retrieval_debug": debug_info
        }

    def process_query_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        filter_doc_id: Optional[str] = None
    ):
        """Generator yielding SSE JSON payloads progressively with observability logging."""
        t0 = time.perf_counter()

        session = self._get_or_create_session(session_id, title=query[:30])
        history = self._get_history_messages(session.id)
        analyzed_query: AnalyzedQuery = QueryAnalyzer.analyze(query, conversation_history=history)

        t_ret_start = time.perf_counter()
        raw_candidates = self.retriever.retrieve(
            analyzed_query=analyzed_query,
            top_k=settings.RETRIEVAL_TOP_K,
            alpha=settings.DENSE_WEIGHT,
            beta=settings.LEXICAL_WEIGHT,
            filter_doc_id=filter_doc_id
        )
        t_ret_end = time.perf_counter()

        t_rerank_start = time.perf_counter()
        reranked_candidates = self.reranker.rerank(raw_candidates, analyzed_query=analyzed_query, top_k=settings.RERANK_TOP_K)
        t_rerank_end = time.perf_counter()

        deduped_candidates = Deduplicator.deduplicate(reranked_candidates, similarity_threshold=settings.DEDUPLICATION_THRESHOLD)
        relevant_candidates = [(chunk, score) for chunk, score in deduped_candidates if score >= settings.RELEVANCE_THRESHOLD]

        context_str, selected_chunks, citations, token_count = self.context_engine.build_context(
            relevant_candidates,
            token_budget=settings.CONTEXT_TOKEN_LIMIT
        )

        retrieval_latency_ms = round((t_ret_end - t_ret_start) * 1000, 2)
        reranking_latency_ms = round((t_rerank_end - t_rerank_start) * 1000, 2)
        source_ids = list({c.get("document_id") for c in citations if c.get("document_id")})

        debug_info = {
            "original_query": analyzed_query.original_query,
            "rewritten_query": analyzed_query.rewritten_query,
            "expanded_queries": analyzed_query.expanded_queries,
            "retrieved_candidates_count": len(raw_candidates),
            "reranked_candidates_count": len(reranked_candidates),
            "selected_context_count": len(selected_chunks),
            "context_token_count": token_count,
            "retrieval_latency_ms": retrieval_latency_ms,
            "reranking_latency_ms": reranking_latency_ms,
            "intent": analyzed_query.intent,
            "extracted_keywords": analyzed_query.keywords,
            "source_ids": source_ids,
        }

        # Yield metadata first
        meta_payload = {
            "type": "meta",
            "session_id": session.id,
            "query": query,
            "rewritten_query": analyzed_query.rewritten_query,
            "sources": citations,
            "retrieval_debug": debug_info
        }
        yield f"data: {json.dumps(meta_payload)}\n\n"

        t_llm_start = time.perf_counter()
        full_response_text = ""
        if not context_str.strip():
            no_info_msg = "I could not find sufficient information in the provided sources to answer this reliably."
            full_response_text = no_info_msg
            yield f"data: {json.dumps({'type': 'token', 'token': no_info_msg})}\n\n"
        else:
            prompt = f"Retrieved Context:\n{context_str}\n\nUser Query: {analyzed_query.rewritten_query}"
            for token in self.llm.stream(prompt=prompt, system_instruction=SYSTEM_RAG_INSTRUCTION, temperature=0.2):
                full_response_text += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        t_llm_end = time.perf_counter()
        llm_latency_ms = round((t_llm_end - t_llm_start) * 1000, 2)

        # Save to DB
        user_msg = ChatMessageModel(session_id=session.id, role="user", content=query)
        assistant_msg = ChatMessageModel(
            session_id=session.id,
            role="assistant",
            content=full_response_text,
            msg_metadata={"sources": citations}
        )
        self.db.add_all([user_msg, assistant_msg])
        self.db.commit()

        # Observability logging
        logger.log_observability("rag_stream_execution", {
            "session_id": session.id,
            "query": query,
            "retrieval_latency_ms": retrieval_latency_ms,
            "reranking_latency_ms": reranking_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "total_latency_ms": round((t_llm_end - t0) * 1000, 2),
            "retrieved_chunk_count": len(raw_candidates),
            "reranked_chunk_count": len(reranked_candidates),
            "selected_chunk_count": len(selected_chunks),
            "context_token_count": token_count,
            "source_ids": source_ids,
        })

        yield "data: [DONE]\n\n"



import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.database import ChatSessionModel, ChatMessageModel
from app.retrieval.query_analyzer import QueryAnalyzer, AnalyzedQuery
from app.retrieval.retriever import HybridRetriever
from app.ranking.reranker import Reranker
from app.ranking.deduplicator import Deduplicator
from app.context.context_engine import ContextEngine
from app.llm.factory import LLMFactory
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
    """End-to-end Multimodal RAG Query and Conversational Service."""

    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.reranker = Reranker(top_k=8)
        self.context_engine = ContextEngine(context_budget_tokens=4000)
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
        filter_doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline:
        Query -> Conversation Resolution -> Analysis -> Hybrid Retrieval -> Reranking -> Deduplication -> Context Engine -> LLM -> Citations.
        """
        # 1. Chat Session & History
        session = self._get_or_create_session(session_id, title=query[:30])
        history = self._get_history_messages(session.id)

        # 2. Query Understanding & Conversational Resolution
        analyzed_query: AnalyzedQuery = QueryAnalyzer.analyze(query, conversation_history=history)

        # 3. Hybrid Retrieval (Dense Vector + BM25 Lexical)
        raw_candidates = self.retriever.retrieve(
            analyzed_query=analyzed_query,
            top_k=25,
            filter_doc_id=filter_doc_id
        )

        # 4. Re-ranking
        reranked_candidates = self.reranker.rerank(raw_candidates, analyzed_query=analyzed_query, top_k=10)

        # 5. Deduplication & Relevance Thresholding
        deduped_candidates = Deduplicator.deduplicate(reranked_candidates, similarity_threshold=0.82)
        relevant_candidates = [(chunk, score) for chunk, score in deduped_candidates if score >= 0.15]

        # 6. Context Engine (Lost-in-the-middle ordering + Token budgeting + Formatting)
        context_str, selected_chunks, citations, token_count = self.context_engine.build_context(
            relevant_candidates,
            token_budget=4000
        )


        # 7. LLM Generation
        if not context_str.strip():
            answer = "I could not find sufficient information in the provided sources to answer this reliably."
        else:
            prompt = f"Retrieved Context:\n{context_str}\n\nUser Query: {analyzed_query.rewritten_query}"
            answer = self.llm.generate(
                prompt=prompt,
                system_instruction=SYSTEM_RAG_INSTRUCTION,
                temperature=0.2
            )

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

        # 9. Debug metadata payload
        debug_info = {
            "original_query": analyzed_query.original_query,
            "rewritten_query": analyzed_query.rewritten_query,
            "expanded_queries": analyzed_query.expanded_queries,
            "retrieved_candidates_count": len(raw_candidates),
            "reranked_candidates_count": len(reranked_candidates),
            "selected_context_count": len(selected_chunks),
            "context_token_count": token_count,
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

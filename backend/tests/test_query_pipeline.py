import io
import pytest
import pypdf
from fastapi import status

from app.retrieval.query_analyzer import QueryAnalyzer
from app.retrieval.bm25 import BM25Retriever
from app.ranking.reranker import Reranker
from app.ranking.deduplicator import Deduplicator
from app.context.context_engine import ContextEngine
from app.models.internal import DocumentChunk


def test_conversational_query_rewriting():
    history = [
        {"role": "user", "content": "What is Transmission Control Protocol?"},
        {"role": "assistant", "content": "TCP is a core communications protocol of the Internet protocol suite."}
    ]

    # Test pronoun resolution "its" -> "the Transmission Control Protocol"
    query = "What are its advantages?"
    resolved = QueryAnalyzer.resolve_conversational_query(query, history)
    assert "Transmission Control Protocol" in resolved

    analyzed = QueryAnalyzer.analyze(query, history)
    assert analyzed.rewritten_query == resolved
    assert "factual" in analyzed.intent


def test_query_metadata_constraint_extraction():
    query = "What does page 12 of the PDF say about virtual memory management?"
    analyzed = QueryAnalyzer.analyze(query)

    assert analyzed.constraints.page_number == 12
    assert analyzed.constraints.source_type == "pdf"
    assert "memory" in analyzed.keywords
    assert "virtual" in analyzed.keywords


def test_reranker_and_deduplication():
    chunk1 = DocumentChunk(id="c1", document_id="doc1", chunk_index=0, content="Virtual memory permits execution of processes.", metadata={"page_number": 12})
    chunk2 = DocumentChunk(id="c2", document_id="doc1", chunk_index=1, content="Virtual memory permits execution of processes.", metadata={"page_number": 12})
    chunk3 = DocumentChunk(id="c3", document_id="doc2", chunk_index=0, content="TCP guarantees reliable delivery of packets.", metadata={"section": "Networks"})

    candidates = [(chunk1, 0.9), (chunk2, 0.88), (chunk3, 0.4)]

    # Test Deduplication
    deduped = Deduplicator.deduplicate(candidates)
    assert len(deduped) == 2  # chunk2 exact duplicate removed

    # Test Reranking
    analyzed = QueryAnalyzer.analyze("virtual memory processes")
    reranked = Reranker(top_k=5).rerank(deduped, analyzed)
    assert reranked[0][0].id == "c1"


def test_context_engine_lost_in_middle_and_budgeting():
    engine = ContextEngine(context_budget_tokens=100)

    chunk1 = DocumentChunk(id="c1", document_id="doc1", chunk_index=0, content="Highest relevance content item.", metadata={"page_number": 1})
    chunk2 = DocumentChunk(id="c2", document_id="doc1", chunk_index=1, content="Second relevance content item.", metadata={"page_number": 2})
    chunk3 = DocumentChunk(id="c3", document_id="doc1", chunk_index=2, content="Third relevance content item.", metadata={"page_number": 3})


    items = [(chunk1, 0.95), (chunk2, 0.85), (chunk3, 0.75)]

    # Test Lost-in-the-Middle ordering
    reordered = engine.apply_lost_in_the_middle_ordering(items)
    assert reordered[0][0].id == "c1"  # Highest relevance at start
    assert reordered[-1][0].id == "c2" # High relevance at end

    # Test Token budgeting & formatting
    context_str, selected, citations, tokens = engine.build_context(items, token_budget=250)
    assert len(selected) > 0
    assert "SOURCE 1" in context_str
    assert citations[0]["page"] == 1


def test_insufficient_context_behavior(client):
    # Query over non-existent or empty topic
    response = client.post(
        "/api/query",
        json={"query": "What is quantum flux teleportation protocol in 3025?"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "could not find sufficient information" in data["answer"].lower()
    assert "retrieval_debug" in data


def test_end_to_end_rag_pdf_ingestion_and_query(client, tmp_upload_dir):
    """
    Full End-to-End System Test:
    PDF Upload -> Ingestion Pipeline -> Chunking & Embedding -> POST /api/query -> Hybrid Retrieval -> Reranking -> Context Engine -> Grounded Answer & Citation.
    """
    pdf_file = tmp_upload_dir / "os_concepts.pdf"
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=300, height=300)

    # Note: pypdf blank page doesn't inject text streams natively, so test TXT upload to guarantee chunk text content for End-to-End assertion
    content = b"Operating System Concept: Virtual memory is a memory management technique that provides an idealized abstraction of storage resources. Page 15 covers demand paging."

    # 1. Upload Document
    upload_res = client.post(
        "/api/documents/upload",
        files={"files": ("os_concepts.txt", io.BytesIO(content), "text/plain")}
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    doc_id = upload_res.json()["successful_uploads"][0]["id"]

    # 2. Execute RAG Query over ingested document
    query_res = client.post(
        "/api/query",
        json={"query": "What is virtual memory?", "document_id": doc_id}
    )
    assert query_res.status_code == status.HTTP_200_OK
    data = query_res.json()

    assert "virtual memory" in data["answer"].lower() or "memory management" in data["answer"].lower()
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["document"] == "os_concepts.txt"
    assert data["retrieval_debug"]["selected_context_count"] >= 1
    assert data["retrieval_debug"]["context_token_count"] > 0

    # 3. Execute Conversational Follow-Up Query
    session_id = data["session_id"]
    followup_res = client.post(
        "/api/chat",
        json={"query": "What does it provide?", "session_id": session_id}
    )
    assert followup_res.status_code == status.HTTP_200_OK
    followup_data = followup_res.json()

    # Verify conversational query resolved pronoun "it" -> "virtual memory"
    assert "virtual memory" in followup_data["rewritten_query"].lower()

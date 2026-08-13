from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import RAGQueryService

router = APIRouter(prefix="", tags=["Query & Chat"])


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
@router.post("/chat", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def process_rag_query(
    payload: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute full RAG Retrieval & Generation pipeline:
    Query -> Conversation Resolution -> Analysis -> Hybrid Search (Vector + BM25) -> Reranking -> Deduplication -> Lost-in-the-Middle Context Engine -> LLM -> Citations.
    """
    service = RAGQueryService(db)
    result = service.process_query(
        query=payload.query,
        session_id=payload.session_id,
        filter_doc_id=payload.document_id
    )
    return result

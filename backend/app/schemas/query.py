from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="User question or prompt for RAG system")
    session_id: Optional[str] = Field(None, description="Optional chat session ID for conversational follow-ups")
    document_id: Optional[str] = Field(None, description="Optional document ID to restrict retrieval scope")
    top_k: Optional[int] = Field(None, description="Configurable top-k candidate chunks for retrieval")
    rerank_k: Optional[int] = Field(None, description="Configurable top-k candidate chunks for reranking")
    context_budget: Optional[int] = Field(None, description="Configurable token limit for context engine")



class CitationItem(BaseModel):
    document: str
    source_type: str
    chunk_id: str
    score: float
    page: Optional[int] = None
    slide: Optional[int] = None
    url: Optional[str] = None
    section: Optional[str] = None


class RetrievalDebugInfo(BaseModel):
    original_query: str
    rewritten_query: str
    expanded_queries: List[str]
    retrieved_candidates_count: int
    reranked_candidates_count: int
    selected_context_count: int
    context_token_count: int
    intent: str
    extracted_keywords: List[str]


class QueryResponse(BaseModel):
    session_id: str
    query: str
    rewritten_query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_debug: RetrievalDebugInfo

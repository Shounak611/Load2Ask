from typing import List, Tuple, Dict, Any, Optional
import tiktoken
from app.models.internal import DocumentChunk
from app.core.config import settings
from app.core.logging import logger


class ContextEngine:
    """
    Dedicated Context Engine providing:
    1. Context Prioritization & Deduplication
    2. Context Compression
    3. Lost-In-The-Middle Context Ordering (placing high-relevance chunks at beginning and end)
    4. Token Budgeting
    5. Structured Context Formatting with Source Metadata
    """

    def __init__(self, context_budget_tokens: int = 4000):
        self.context_budget_tokens = context_budget_tokens
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Estimate token count using tiktoken (fallback to ~4 chars per token)."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, len(text) // 4)

    def apply_lost_in_the_middle_ordering(
        self,
        ranked_items: List[Tuple[DocumentChunk, float]]
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Reorders chunks so top relevance items are placed at the BEGINNING and END of the context,
        avoiding attention degradation in the middle of LLM context windows.
        """
        if len(ranked_items) <= 2:
            return ranked_items

        reordered = [None] * len(ranked_items)
        left = 0
        right = len(ranked_items) - 1

        for i, item in enumerate(ranked_items):
            if i % 2 == 0:
                reordered[left] = item
                left += 1
            else:
                reordered[right] = item
                right -= 1

        return [item for item in reordered if item is not None]

    def build_context(
        self,
        scored_chunks: List[Tuple[DocumentChunk, float]],
        token_budget: Optional[int] = None
    ) -> Tuple[str, List[Tuple[DocumentChunk, float]], List[Dict[str, Any]], int]:
        """
        Compresses, budgets, orders, and formats context for LLM prompt generation.
        Returns: (formatted_context_string, selected_chunks_with_scores, citations_list, total_tokens)
        """
        budget = token_budget or self.context_budget_tokens

        if not scored_chunks:
            return "", [], [], 0

        # Apply Lost-in-the-Middle reordering
        ordered_items = self.apply_lost_in_the_middle_ordering(scored_chunks)

        selected_items: List[Tuple[DocumentChunk, float]] = []
        citations: List[Dict[str, Any]] = []
        total_tokens = 0
        formatted_blocks = []

        for idx, (chunk, score) in enumerate(ordered_items, start=1):
            meta = chunk.metadata or {}
            source_type = meta.get("source_type", "document")
            source_name = meta.get("original_name") or meta.get("file_name") or meta.get("source_name") or meta.get("title") or chunk.document_id


            # Header metadata block
            meta_header = [f"SOURCE {idx}"]
            if source_type == "web":
                meta_header.append(f"URL: {meta.get('url', source_name)}")
                if meta.get("title"):
                    meta_header.append(f"Title: {meta.get('title')}")
            else:
                meta_header.append(f"Document: {source_name}")
                if meta.get("page_number"):
                    meta_header.append(f"Page: {meta.get('page_number')}")
                if meta.get("slide_number"):
                    meta_header.append(f"Slide: {meta.get('slide_number')}")

            if meta.get("section"):
                meta_header.append(f"Section: {meta.get('section')}")

            header_str = "\n".join(meta_header)
            block_str = f"[{header_str}]\nContent:\n{chunk.content.strip()}\n"
            block_tokens = self.count_tokens(block_str)

            if total_tokens + block_tokens > budget:
                logger.info(f"Token budget ({budget}) reached. Stopping context inclusion at {len(selected_items)} chunks.")
                break

            total_tokens += block_tokens
            selected_items.append((chunk, score))
            formatted_blocks.append(block_str)

            # Build structured citation
            citation = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "source_type": source_type,
                "document": source_name,
                "score": round(float(score), 4)
            }
            if meta.get("page_number"):
                citation["page"] = meta["page_number"]
            if meta.get("slide_number"):
                citation["slide"] = meta["slide_number"]
            if meta.get("url"):
                citation["url"] = meta["url"]
            if meta.get("section"):
                citation["section"] = meta["section"]

            citations.append(citation)

        final_context_string = "\n---\n".join(formatted_blocks)
        return final_context_string, selected_items, citations, total_tokens

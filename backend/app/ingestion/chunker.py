import uuid
from typing import List, Dict, Any, Optional
from app.models.internal import Document, DocumentChunk
from app.core.config import settings


class ConfigurableChunker:
    """Configurable text chunker supporting recursive, heading-aware, and document-type-aware splitting."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        # Estimate ~4 chars per token for character-based chunking equivalent
        self.char_chunk_size = self.chunk_size * 4
        self.char_overlap = self.chunk_overlap * 4
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def _split_text(self, text: str) -> List[str]:
        """Recursive character text splitting logic."""
        if len(text) <= self.char_chunk_size:
            return [text] if text.strip() else []

        # Find best separator
        selected_sep = ""
        for sep in self.separators:
            if sep in text:
                selected_sep = sep
                break

        if not selected_sep:
            # Fallback hard slice
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.char_chunk_size, len(text))
                chunks.append(text[start:end])
                start += self.char_chunk_size - self.char_overlap
            return chunks

        parts = text.split(selected_sep)
        chunks = []
        current_chunk = ""

        for part in parts:
            candidate = f"{current_chunk}{selected_sep}{part}" if current_chunk else part
            if len(candidate) <= self.char_chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(part) > self.char_chunk_size:
                    # Recursively split oversized part
                    sub_chunks = self._split_text(part)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = part

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Merge overlapping chunks if overlap is configured
        if self.char_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i > 0 and len(chunks[i - 1]) >= self.char_overlap:
                    overlap_prefix = chunks[i - 1][-self.char_overlap:]
                    chunk = f"... {overlap_prefix} {chunk}"
                overlapped_chunks.append(chunk)
            return overlapped_chunks

        return chunks

    def chunk_document(self, doc: Document) -> List[DocumentChunk]:
        """
        Split a Document into DocumentChunks, preserving metadata (page_number, slide_number, section, etc.).
        """
        raw_chunks = self._split_text(doc.content)
        result_chunks: List[DocumentChunk] = []

        for idx, text in enumerate(raw_chunks):
            if not text.strip():
                continue

            # Merge document metadata into chunk metadata
            chunk_meta = dict(doc.metadata or {})
            chunk_meta.update({
                "document_id": doc.id,
                "source_type": doc.source_type,
                "source_name": doc.source_name,
                "source_uri": doc.source_uri,
                "chunk_index": idx,
            })

            # Format-specific metadata extractions if present in metadata dictionary
            if "page_number" in doc.metadata:
                chunk_meta["page_number"] = doc.metadata["page_number"]
            if "slide_number" in doc.metadata:
                chunk_meta["slide_number"] = doc.metadata["slide_number"]
            if "section" in doc.metadata:
                chunk_meta["section"] = doc.metadata["section"]

            result_chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc.id,
                    content=text,
                    chunk_index=idx,
                    metadata=chunk_meta,
                )
            )

        return result_chunks

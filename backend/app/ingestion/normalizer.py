import re
from app.models.internal import Document


class DocumentNormalizer:
    """Normalizes raw text extracted from documents while retaining structural markers."""

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""

        # Remove null bytes and non-printable control characters (except newline, tab)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # Standardize line endings (\r\n -> \n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]

        # Reduce 3+ consecutive blank lines to at most 2 blank lines
        normalized_lines = []
        consecutive_blanks = 0
        for line in lines:
            if not line:
                consecutive_blanks += 1
                if consecutive_blanks <= 2:
                    normalized_lines.append(line)
            else:
                consecutive_blanks = 0
                normalized_lines.append(line)

        return '\n'.join(normalized_lines).strip()

    @classmethod
    def normalize(cls, doc: Document) -> Document:
        """Return a copy of the Document with normalized content."""
        normalized_content = cls.normalize_text(doc.content)
        return Document(
            id=doc.id,
            source_type=doc.source_type,
            source_name=doc.source_name,
            source_uri=doc.source_uri,
            content=normalized_content,
            metadata=dict(doc.metadata or {})
        )

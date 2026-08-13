import re
from pathlib import Path
from typing import Union, Dict, Any
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger


class MarkdownLoader(BaseLoader):
    """Markdown document loader extracting headings, code blocks, and body text."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"Markdown file not found: {source}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            headings = [line.strip() for line in content.splitlines() if re.match(r'^#{1,6}\s+', line.strip())]

            meta = {
                "source_type": "markdown",
                "file_name": file_path.name,
                "headings": headings[:10],
                "file_size": file_path.stat().st_size,
                **(metadata or {})
            }

            return Document(
                source_type="markdown",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=content,
                metadata=meta
            )
        except Exception as e:
            logger.error(f"Failed to load Markdown file {source}: {e}")
            raise InvalidFileError(f"Failed to read Markdown file {source}: {str(e)}")

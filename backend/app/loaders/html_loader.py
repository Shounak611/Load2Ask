from pathlib import Path
from typing import Union, Dict, Any
from bs4 import BeautifulSoup
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger


class HTMLLoader(BaseLoader):
    """Local HTML file loader using BeautifulSoup for clean text and heading extraction."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"HTML file not found: {source}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html_raw = f.read()

            soup = BeautifulSoup(html_raw, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else file_path.name

            headings = [
                h.get_text().strip()
                for h in soup.find_all(["h1", "h2", "h3"])
                if h.get_text().strip()
            ]

            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
                element.decompose()

            lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            meta = {
                "source_type": "html",
                "file_name": file_path.name,
                "title": title,
                "headings": headings[:10],
                "file_size": file_path.stat().st_size,
                **(metadata or {})
            }

            return Document(
                source_type="html",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=f"# {title}\n\n{clean_text}",
                metadata=meta
            )
        except Exception as e:
            logger.error(f"Failed to load HTML file {source}: {e}")
            raise InvalidFileError(f"Failed to read HTML file {source}: {str(e)}")

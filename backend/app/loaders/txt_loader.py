import os
from pathlib import Path
from typing import Union, Dict, Any
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError


class TextLoader(BaseLoader):
    """Loader for plain text files (.txt)."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"File not found: {source}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            meta = {
                "file_size": file_path.stat().st_size,
                "extension": file_path.suffix,
                **(metadata or {})
            }

            return Document(
                source_type="txt",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=content,
                metadata=meta
            )
        except Exception as e:
            raise InvalidFileError(f"Failed to read text file {source}: {str(e)}")

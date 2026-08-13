import json
from pathlib import Path
from typing import Union, Dict, Any
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger


class JSONLoader(BaseLoader):
    """JSON file loader serializing structured objects into readable key-value representations."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"JSON file not found: {source}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            if isinstance(data, dict):
                keys = list(data.keys())
                formatted_content = json.dumps(data, indent=2)
            elif isinstance(data, list):
                keys = list(data[0].keys()) if data and isinstance(data[0], dict) else []
                formatted_content = json.dumps(data, indent=2)
            else:
                keys = []
                formatted_content = str(data)

            meta = {
                "source_type": "json",
                "file_name": file_path.name,
                "top_level_keys": keys,
                "file_size": file_path.stat().st_size,
                **(metadata or {})
            }

            return Document(
                source_type="json",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=formatted_content,
                metadata=meta
            )
        except Exception as e:
            logger.error(f"Failed to load JSON file {source}: {e}")
            raise InvalidFileError(f"Failed to read JSON file {source}: {str(e)}")

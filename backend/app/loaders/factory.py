from typing import Dict, Type
from pathlib import Path
from app.loaders.base import BaseLoader
from app.loaders.txt_loader import TextLoader
from app.loaders.pdf_loader import PDFLoader
from app.loaders.image_loader import ImageLoader
from app.loaders.web_loader import WebLoader
from app.loaders.docx_loader import DOCXLoader
from app.loaders.pptx_loader import PPTXLoader
from app.loaders.csv_loader import CSVLoader
from app.loaders.xlsx_loader import XLSXLoader
from app.loaders.json_loader import JSONLoader
from app.loaders.markdown_loader import MarkdownLoader
from app.loaders.html_loader import HTMLLoader
from app.core.errors import UnsupportedFormatError


class LoaderFactory:
    """Registry and factory for document loaders based on file extensions or source type strings."""

    _registry: Dict[str, Type[BaseLoader]] = {
        "txt": TextLoader,
        "pdf": PDFLoader,
        "png": ImageLoader,
        "jpg": ImageLoader,
        "jpeg": ImageLoader,
        "image": ImageLoader,
        "web": WebLoader,
        "url": WebLoader,
        "docx": DOCXLoader,
        "pptx": PPTXLoader,
        "csv": CSVLoader,
        "xlsx": XLSXLoader,
        "json": JSONLoader,
        "md": MarkdownLoader,
        "markdown": MarkdownLoader,
        "html": HTMLLoader,
        "htm": HTMLLoader,
    }

    @classmethod
    def register(cls, source_type: str, loader_cls: Type[BaseLoader]):
        """Register a new custom loader for a given source type or extension."""
        cls._registry[source_type.lower()] = loader_cls

    @classmethod
    def get_loader(cls, source_type_or_extension: str) -> BaseLoader:
        """Instantiate and return the appropriate loader for a given file type/extension."""
        key = source_type_or_extension.lower().lstrip(".")
        loader_cls = cls._registry.get(key)

        if not loader_cls:
            raise UnsupportedFormatError(f"No loader registered for format '{source_type_or_extension}'")

        return loader_cls()

    @classmethod
    def get_loader_for_file(cls, file_path: str) -> BaseLoader:
        """Infer loader based on file extension."""
        ext = Path(file_path).suffix.lower()
        if not ext:
            raise UnsupportedFormatError(f"Could not infer file extension from path: {file_path}")
        return cls.get_loader(ext)

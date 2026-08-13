import os
import io
from pathlib import Path

from typing import Union, Dict, Any, List
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None
    Image = None


class PDFLoader(BaseLoader):
    """PDF loader supporting text extraction, scanned PDF detection, OCR fallback, and metadata tagging."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"PDF file not found: {source}")

        if pypdf is None:
            raise InvalidFileError("pypdf package is not installed.")

        try:
            reader = pypdf.PdfReader(str(file_path))
            num_pages = len(reader.pages)
            pages_extracted = []
            is_scanned = False
            total_chars = 0

            for i, page in enumerate(reader.pages):
                page_num = i + 1
                text = page.extract_text() or ""
                clean_text = text.strip()
                total_chars += len(clean_text)

                if clean_text:
                    pages_extracted.append(f"[Page {page_num}]\n{clean_text}")
                else:
                    pages_extracted.append(f"[Page {page_num}]\n(Empty page text)")

            # Scanned PDF detection: if average text per page is < 15 chars, attempt OCR fallback if images exist
            avg_chars = total_chars / max(num_pages, 1)
            if avg_chars < 15:
                is_scanned = True
                logger.info(f"PDF {file_path.name} appears to be scanned (avg chars/page: {avg_chars:.1f}). Attempting OCR fallback...")
                
                if pytesseract is not None and Image is not None:
                    ocr_pages = []
                    for i, page in enumerate(reader.pages):
                        page_num = i + 1
                        ocr_text = ""
                        try:
                            for img_obj in page.images:
                                image = Image.open(io.BytesIO(img_obj.data))
                                extracted = pytesseract.image_to_string(image)
                                if extracted.strip():
                                    ocr_text += extracted + "\n"
                        except Exception as ocr_err:
                            logger.warning(f"OCR failed for page {page_num} in {file_path.name}: {ocr_err}")

                        if ocr_text.strip():
                            ocr_pages.append(f"[Page {page_num} - OCR]\n{ocr_text.strip()}")
                        else:
                            ocr_pages.append(pages_extracted[i])

                    if any("[Page" in p and "OCR]" in p for p in ocr_pages):
                        pages_extracted = ocr_pages

            full_content = "\n\n".join(pages_extracted)

            meta = {
                "source_type": "pdf",
                "file_name": file_path.name,
                "num_pages": num_pages,
                "is_scanned": is_scanned,
                "file_size": file_path.stat().st_size,
                "extension": file_path.suffix,
                **(metadata or {})
            }

            return Document(
                source_type="pdf",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=full_content,
                metadata=meta
            )
        except Exception as e:
            logger.error(f"Failed to process PDF {source}: {e}")
            raise InvalidFileError(f"Failed to parse PDF file {source}: {str(e)}")

from pathlib import Path
from typing import Union, Dict, Any
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


class ImageLoader(BaseLoader):
    """Image document loader using PIL and PyTesseract for OCR text extraction and visual metadata."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"Image file not found: {source}")

        if Image is None:
            raise InvalidFileError("PIL (Pillow) package is not installed.")

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                img_format = img.format or file_path.suffix.lstrip(".").upper()
                img_mode = img.mode

                extracted_text = ""
                ocr_success = False

                if pytesseract is not None:
                    try:
                        text = pytesseract.image_to_string(img)
                        if text and text.strip():
                            extracted_text = text.strip()
                            ocr_success = True
                    except Exception as ocr_err:
                        logger.warning(f"PyTesseract OCR failed for {file_path.name}: {ocr_err}")

                if not extracted_text:
                    extracted_text = (
                        f"[Image: {file_path.name}]\n"
                        f"Format: {img_format}, Dimensions: {width}x{height} pixels, Mode: {img_mode}.\n"
                        f"No OCR text content was detected in this image."
                    )

                meta = {
                    "source_type": "image",
                    "file_name": file_path.name,
                    "width": width,
                    "height": height,
                    "format": img_format,
                    "mode": img_mode,
                    "ocr_success": ocr_success,
                    "file_size": file_path.stat().st_size,
                    **(metadata or {})
                }

                return Document(
                    source_type="image",
                    source_name=file_path.name,
                    source_uri=str(file_path.absolute()),
                    content=extracted_text,
                    metadata=meta
                )
        except Exception as e:
            logger.error(f"Failed to process image {source}: {e}")
            raise InvalidFileError(f"Failed to read image file {source}: {str(e)}")

import os
import re
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.storage.base import StorageProvider
from app.core.config import settings
from app.core.errors import InvalidFileError, Load2AskException
from app.core.logging import logger

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".png", ".jpg", ".jpeg", ".docx", ".pptx",
    ".csv", ".xlsx", ".json", ".md", ".markdown", ".html", ".htm"
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and null-byte injection."""
    filename = filename.replace("\x00", "")
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename or "uploaded_file"


class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of StorageProvider with security checks."""

    def __init__(self, upload_dir: str = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIRECTORY).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, file: UploadFile) -> Tuple[str, str, int]:
        if not file.filename:
            raise InvalidFileError("Uploaded file has no filename.")

        safe_filename = sanitize_filename(file.filename)
        ext = Path(safe_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(f"Extension '{ext}' is not permitted. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        unique_name = f"{uuid.uuid4()}{ext}"
        target_path = (self.upload_dir / unique_name).resolve()

        if not str(target_path).startswith(str(self.upload_dir)):
            raise InvalidFileError("Path traversal attack detected in file path.")

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        try:
            bytes_written = 0
            with target_path.open("wb") as buffer:
                while chunk := file.file.read(1024 * 1024):
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        target_path.unlink(missing_ok=True)
                        raise InvalidFileError(f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.")
                    buffer.write(chunk)

            logger.info(f"LocalStorageProvider saved file '{safe_filename}' to {target_path} ({bytes_written} bytes)")
            return str(target_path), safe_filename, bytes_written
        except InvalidFileError:
            raise
        except Exception as e:
            logger.error(f"Failed to save upload file {safe_filename}: {e}")
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise Load2AskException(f"Failed to save file to local disk: {str(e)}")

    def download(self, storage_uri: str) -> bytes:
        path = Path(storage_uri).resolve()
        if not path.exists():
            raise Load2AskException(f"File at {storage_uri} does not exist.")
        return path.read_bytes()

    def delete(self, storage_uri: str) -> bool:
        try:
            path = Path(storage_uri).resolve()
            if not str(path).startswith(str(self.upload_dir)):
                logger.warning(f"Prevented deletion attempt outside upload directory: {storage_uri}")
                return False
            if path.exists():
                path.unlink()
                logger.info(f"LocalStorageProvider deleted file {storage_uri}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {storage_uri}: {e}")
            return False

    def exists(self, storage_uri: str) -> bool:
        try:
            return Path(storage_uri).exists()
        except Exception:
            return False

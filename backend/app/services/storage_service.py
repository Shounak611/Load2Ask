import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings
from app.core.errors import InvalidFileError, Load2AskException
from app.core.logging import logger


class StorageService:
    """Handles local disk persistence for uploaded documents."""

    def __init__(self, upload_dir: str = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload_file(self, file: UploadFile) -> tuple[str, str, int]:
        """
        Saves uploaded file to upload_dir with a unique filename.
        Returns tuple of (file_path, original_filename, file_size).
        """
        if not file.filename:
            raise InvalidFileError("Uploaded file has no filename.")

        # Clean filename and generate storage path
        ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        target_path = self.upload_dir / unique_name

        try:
            with target_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = target_path.stat().st_size
            logger.info(f"Saved file {file.filename} to {target_path} ({file_size} bytes)")
            return str(target_path.absolute()), file.filename, file_size
        except Exception as e:
            logger.error(f"Failed to save upload file {file.filename}: {e}")
            raise Load2AskException(f"Failed to save file to disk: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk if it exists."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

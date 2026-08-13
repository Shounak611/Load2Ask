from abc import ABC, abstractmethod
from typing import Tuple
from fastapi import UploadFile


class StorageProvider(ABC):
    """Abstract interface for permanent and ephemeral document file storage."""

    @abstractmethod
    def upload(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Upload/save file.
        Returns tuple of (storage_uri, sanitized_filename, file_size_in_bytes).
        """
        pass

    @abstractmethod
    def download(self, storage_uri: str) -> bytes:
        """Download file content as raw bytes."""
        pass

    @abstractmethod
    def delete(self, storage_uri: str) -> bool:
        """Delete file at storage_uri."""
        pass

    @abstractmethod
    def exists(self, storage_uri: str) -> bool:
        """Check if file exists at storage_uri."""
        pass

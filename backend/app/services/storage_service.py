from typing import Tuple, Optional
from fastapi import UploadFile
from app.storage.base import StorageProvider
from app.storage.factory import StorageFactory


class StorageService:
    """Production service delegating file and document storage operations to StorageProvider abstraction."""

    def __init__(self, provider: Optional[StorageProvider] = None):
        self.provider = provider or StorageFactory.get_storage_provider()

    def save_upload_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """Upload file via active StorageProvider."""
        return self.provider.upload(file)

    def download_file(self, storage_uri: str) -> bytes:
        """Download file bytes via active StorageProvider."""
        return self.provider.download(storage_uri)

    def delete_file(self, storage_uri: str) -> bool:
        """Delete file via active StorageProvider."""
        return self.provider.delete(storage_uri)

    def file_exists(self, storage_uri: str) -> bool:
        """Check if file exists via active StorageProvider."""
        return self.provider.exists(storage_uri)

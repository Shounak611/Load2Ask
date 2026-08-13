from typing import Optional
from app.storage.base import StorageProvider
from app.storage.local_storage import LocalStorageProvider
from app.storage.s3_storage import S3StorageProvider
from app.core.config import settings
from app.core.logging import logger


class StorageFactory:
    """Factory for instantiating the configured StorageProvider."""

    @staticmethod
    def get_storage_provider(provider_name: Optional[str] = None) -> StorageProvider:
        name = (provider_name or settings.STORAGE_PROVIDER or "local").lower()

        if name == "s3" or (settings.S3_BUCKET_NAME and name != "local"):
            try:
                logger.info("Initializing S3StorageProvider via factory.")
                return S3StorageProvider()
            except Exception as e:
                logger.warning(f"S3StorageProvider initialization failed ({e}). Falling back to LocalStorageProvider.")
                return LocalStorageProvider()
        else:
            logger.info("Initializing LocalStorageProvider via factory.")
            return LocalStorageProvider()

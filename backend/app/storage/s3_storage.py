import os
import uuid
import boto3
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.storage.base import StorageProvider
from app.storage.local_storage import sanitize_filename, ALLOWED_EXTENSIONS
from app.core.config import settings
from app.core.errors import InvalidFileError, Load2AskException
from app.core.logging import logger


class S3StorageProvider(StorageProvider):
    """AWS S3 / S3-compatible Object Storage implementation of StorageProvider."""

    def __init__(
        self,
        bucket_name: str = None,
        region_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ):
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region_name = region_name or settings.S3_REGION
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY

        if not self.bucket_name:
            raise Load2AskException("S3_BUCKET_NAME is required for S3StorageProvider.")

        self.s3_client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def upload(self, file: UploadFile) -> Tuple[str, str, int]:
        if not file.filename:
            raise InvalidFileError("Uploaded file has no filename.")

        safe_filename = sanitize_filename(file.filename)
        ext = Path(safe_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(f"Extension '{ext}' is not permitted.")

        key = f"uploads/{uuid.uuid4()}{ext}"
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        try:
            content = file.file.read()
            file_size = len(content)
            if file_size > max_bytes:
                raise InvalidFileError(f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream"
            )
            s3_uri = f"s3://{self.bucket_name}/{key}"
            logger.info(f"S3StorageProvider uploaded file '{safe_filename}' to {s3_uri}")
            return s3_uri, safe_filename, file_size
        except InvalidFileError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file {safe_filename} to S3: {e}")
            raise Load2AskException(f"S3 upload failed: {str(e)}")

    def download(self, storage_uri: str) -> bytes:
        try:
            key = storage_uri.replace(f"s3://{self.bucket_name}/", "")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to download {storage_uri} from S3: {e}")
            raise Load2AskException(f"S3 download failed: {str(e)}")

    def delete(self, storage_uri: str) -> bool:
        try:
            key = storage_uri.replace(f"s3://{self.bucket_name}/", "")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"S3StorageProvider deleted {storage_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {storage_uri} from S3: {e}")
            return False

    def exists(self, storage_uri: str) -> bool:
        try:
            key = storage_uri.replace(f"s3://{self.bucket_name}/", "")
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

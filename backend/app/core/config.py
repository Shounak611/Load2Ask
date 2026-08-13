import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    LLM_API_KEY: str = "default_llm_key"
    EMBEDDING_API_KEY: str = "default_embedding_key"

    # Database
    DATABASE_URL: str = "sqlite:///./load2ask.db"  # Fallback to SQLite if Postgres is not provided

    # Vector DB
    VECTOR_DB_URL: str = "./chroma_db"
    VECTOR_COLLECTION: str = "load2ask_collection"

    # Uploads
    UPLOAD_DIRECTORY: str = "./uploads"

    # App Config
    APP_NAME: str = "Load2Ask RAG Engine"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Chunking Config
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100
    MAX_FILE_SIZE_MB: int = 50

    # Default embedding provider

    EMBEDDING_PROVIDER: str = "default"  # options: sentence-transformers, openai, mock, default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

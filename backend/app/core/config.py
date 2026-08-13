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

    # Configurable Retrieval & Context Engineering Parameters
    RETRIEVAL_TOP_K: int = 25
    RERANK_TOP_K: int = 10
    CONTEXT_TOKEN_LIMIT: int = 4000
    DENSE_WEIGHT: float = 0.6
    LEXICAL_WEIGHT: float = 0.4
    RELEVANCE_THRESHOLD: float = 0.15
    DEDUPLICATION_THRESHOLD: float = 0.82

    # API Security Config
    API_KEY_REQUIRED: bool = False
    API_KEY: str = "load2ask_secret_key"
    RATE_LIMIT_PER_MINUTE: int = 60

    # Default embedding provider
    EMBEDDING_PROVIDER: str = "default"  # options: sentence-transformers, openai, mock, default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Anchor SQLite path to project root if relative
if settings.DATABASE_URL.startswith("sqlite:///./"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    db_file = settings.DATABASE_URL.replace("sqlite:///./", "")
    settings.DATABASE_URL = f"sqlite:///{os.path.join(base_dir, db_file)}"

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)



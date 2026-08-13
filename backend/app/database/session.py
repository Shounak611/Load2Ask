from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
from app.core.logging import logger

engine_kwargs = {}

if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL / Neon connection pool configuration
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database session in FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema.
    In development / SQLite, creates missing tables automatically.
    In production mode, schema migrations are driven strictly via Alembic.
    """
    if settings.ENVIRONMENT != "production" or settings.DATABASE_URL.startswith("sqlite"):
        from app.database.base import Base
        import app.models.database  # ensure models are imported
        logger.info("Initializing database tables via Base.metadata.create_all()")
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("Production mode detected; table creation managed by Alembic migrations.")

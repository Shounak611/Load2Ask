from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import Load2AskException, load2ask_exception_handler, generic_exception_handler
from app.core.logging import logger
from app.core.security import rate_limit_middleware
from app.database.session import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initialization and cleanup."""
    logger.info("Initializing Load2Ask backend...")
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")

    yield
    logger.info("Shutting down Load2Ask backend.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Multimodal RAG + Context Engineering Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# Register Middlewares
app.middleware("http")(rate_limit_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
app.add_exception_handler(Load2AskException, load2ask_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Routes
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

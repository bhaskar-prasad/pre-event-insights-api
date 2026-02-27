"""FastAPI application initialization and configuration."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db, get_session
from app.routers import example, campaigns
from app.schemas.base import ErrorResponse, ErrorDetail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting application in {settings.ENV} environment")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="FastAPI PostgreSQL Template",
    description="A template for FastAPI with PostgreSQL, SQLAlchemy ORM, and Vault integration",
    version="1.0.0",
    lifespan=lifespan,
)


# Exception handlers for consistent error responses
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with consistent error response."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    error_response = ErrorResponse(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        details=[ErrorDetail(message=str(exc))],
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


# Include routers
app.include_router(example.router)
app.include_router(campaigns.router)


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/v1/health", tags=["health"])
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENV == "development",
        log_level="info",
    )

"""FastAPI application entry point for AgileAI."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from database import engine
from __init__ import Base
from agileai.api.routers import backlog


# ---------------------------------------------------------------------------
# Lifespan events
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AgileAI",
    description="AI-native Agile project management platform",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "agileai-api"},
    )


# ---------------------------------------------------------------------------
# API v1 routes
# ---------------------------------------------------------------------------
app.include_router(
    backlog.router,
    prefix="/api/v1",
)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AgileAI",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agileai.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

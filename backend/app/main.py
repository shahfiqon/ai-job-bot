from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.saved_jobs import router as saved_jobs_router
from app.config import settings
from app.logging_config import setup_logging

# Configure logging with INFO level
setup_logging(log_level="INFO")

app = FastAPI(
    title="Job Apply Assistant API",
    description="Backend services for the Job Apply Assistant Bot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(saved_jobs_router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("FastAPI application for Job Apply Assistant started")
    logger.info(f"API version: {app.version}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS or ['http://localhost:3000', 'http://127.0.0.1:3000']}")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Job Apply Assistant API",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import (
    projects_router,
    documents_router,
    function_points_router,
    testcases_router,
    testscripts_router,
    generator_router
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up E2E Test Generator...")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.LOG_FILE) or "logs", exist_ok=True)
    
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    logger.info("Shutting down E2E Test Generator...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered End-to-End Test Case Generation Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(function_points_router, prefix="/api")
app.include_router(testcases_router, prefix="/api")
app.include_router(testscripts_router, prefix="/api")
app.include_router(generator_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

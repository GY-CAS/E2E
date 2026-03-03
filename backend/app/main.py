from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging_utils import setup_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.console_output import print_step_start, print_step_end, print_success, print_divider
from app.api import (
    projects_router,
    documents_router,
    function_points_router,
    testcases_router,
    testscripts_router,
    generator_router
)

logger = setup_logger("app", json_format=True)


print_divider("E2E Test Generator 启动")
logger.info("Logger initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print_step_start("应用启动", "System")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    print_step_start("初始化数据库连接", "Database")
    await init_db()
    print_step_end("初始化数据库连接", "成功", "Database")

    print_step_end("应用启动", "就绪", "System")

    yield

    print_step_start("应用关闭", "System")

    await close_db()
    print_step_end("数据库连接", "已关闭", "Database")

    print_step_end("应用关闭", "完成", "System")


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

if settings.LOG_API_REQUESTS:
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=settings.LOG_REQUEST_BODY,
        log_response_body=settings.LOG_RESPONSE_BODY,
        log_headers=settings.LOG_HEADERS
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

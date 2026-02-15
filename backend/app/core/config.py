from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "E2E Test Generator"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/e2e_testgen"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "doc_vectors"
    
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"
    
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

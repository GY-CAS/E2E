from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator
import asyncio

DATABASE_URL_SYNC = settings.DATABASE_URL
DATABASE_URL_ASYNC = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_engine(DATABASE_URL_SYNC, echo=settings.DEBUG)

async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=settings.DEBUG)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def get_session():
    with Session(engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db():
    await async_engine.dispose()

"""Database connection management."""

import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

Base = declarative_base()

_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """Initialize database connection."""
    global _engine, _async_session_maker

    logger.info("Initializing database connection", database_url=settings.database_url)

    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.database_echo,
    )

    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("Database connection initialized")


async def close_db() -> None:
    """Close database connection."""
    global _engine, _async_session_maker

    if _engine:
        logger.info("Closing database connection")
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connection closed")


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Get database session context manager."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """Get database session for dependency injection."""
    async with get_db_session() as session:
        yield session

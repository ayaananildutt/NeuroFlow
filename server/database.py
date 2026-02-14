"""
Database Connection & Session Management
Provides async SQLAlchemy engine, session factory, and table initialization.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from models import Base
from config import ServerConfig

logger = logging.getLogger(__name__)

# Async engine for FastAPI endpoints
async_engine = create_async_engine(
    ServerConfig.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for MQTT subscriber thread (paho-mqtt is not async)
sync_engine = create_engine(
    ServerConfig.DATABASE_URL_SYNC,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)


async def init_database() -> None:
    """Create all tables if they don't exist."""
    logger.info("Initializing database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")


async def get_async_session() -> AsyncSession:
    """Dependency for FastAPI routes — yields an async session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def shutdown_database() -> None:
    """Dispose of the async engine on application shutdown."""
    logger.info("Disposing database engine...")
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("Database engine disposed.")

"""
Database - Async SQLAlchemy setup
Uses SQLite for local dev, PostgreSQL for production
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,         # Log SQL queries in dev
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


async def create_tables():
    """Create all tables on startup"""
    async with engine.begin() as conn:
        # Import all models so Base knows about them
        from app.models import video, article, car, consultancy, instagram, users  # noqa
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All database tables created")


async def get_db():
    """Dependency - yields DB session per request"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

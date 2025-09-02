"""Database session management."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..models.base import Base
from .config import DatabaseConfig

logger = logging.getLogger(__name__)

# Global session factory
SessionLocal: Optional[sessionmaker] = None
engine: Optional[Engine] = None


def init_database(config: Optional[DatabaseConfig] = None) -> None:
    """Initialize database connection and create tables."""
    global SessionLocal, engine
    
    if config is None:
        config = DatabaseConfig.from_env()
    
    logger.info(f"Initializing database connection to: {config.url}")
    
    # Create engine
    engine = create_engine(
        config.url,
        echo=config.echo,
        poolclass=QueuePool,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        pool_pre_ping=True,  # Verify connections before use
    )
    
    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session context manager."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


def get_db_session_dependency() -> Session:
    """Get database session for FastAPI dependency injection."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        return db
    finally:
        # Note: Session will be closed by FastAPI dependency system
        pass


async def close_database():
    """Close database connections."""
    global engine
    if engine:
        engine.dispose()
        logger.info("Database connections closed")
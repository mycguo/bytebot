"""Database utilities."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from ..models.base import Base, create_database_engine, create_session_factory


# Global session factory
SessionLocal = None


def init_database(database_url: str = None) -> None:
    """Initialize database connection."""
    global SessionLocal
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
    
    engine = create_database_engine(database_url)
    SessionLocal = create_session_factory(engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_database_session() -> Generator[Session, None, None]:
    """Get database session context manager."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (for dependency injection)."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return SessionLocal()
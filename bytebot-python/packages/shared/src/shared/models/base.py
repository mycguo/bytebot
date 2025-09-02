"""Base database model."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def create_database_engine(database_url: str):
    """Create database engine."""
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL logging in development
        pool_pre_ping=True,
    )
    return engine

def create_session_factory(engine):
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
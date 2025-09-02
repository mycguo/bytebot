"""Task model and related enums."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, String, DateTime, JSON, Enum as SQLEnum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    NEEDS_HELP = "NEEDS_HELP"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskType(str, Enum):
    """Task type enumeration."""
    IMMEDIATE = "IMMEDIATE"
    SCHEDULED = "SCHEDULED"


class Role(str, Enum):
    """Role enumeration."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=False)
    type = Column(SQLEnum(TaskType), default=TaskType.IMMEDIATE, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    control = Column(SQLEnum(Role), default=Role.ASSISTANT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_by = Column(SQLEnum(Role), default=Role.USER, nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    queued_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    model = Column(JSON, nullable=False)  # AI model configuration

    # Relationships
    messages = relationship("Message", back_populates="task", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="task", cascade="all, delete-orphan")
    files = relationship("File", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, description='{self.description[:50]}...', status={self.status})>"
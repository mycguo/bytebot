"""Message model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base
from .task import Role


class Message(Base):
    """Message model."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(JSON, nullable=False)  # Content blocks following Anthropic structure
    role = Column(SQLEnum(Role), default=Role.ASSISTANT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="messages")
    summary = relationship("Summary", back_populates="messages")

    def __repr__(self):
        content_preview = str(self.content)[:100] if self.content else "No content"
        return f"<Message(id={self.id}, role={self.role}, content='{content_preview}...')>"
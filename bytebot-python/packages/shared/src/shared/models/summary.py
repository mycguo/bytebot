"""Summary model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Summary(Base):
    """Summary model."""
    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="summaries")
    messages = relationship("Message", back_populates="summary")
    
    # Self-referential relationship for hierarchy
    parent_summary = relationship("Summary", remote_side=[id], back_populates="child_summaries")
    child_summaries = relationship("Summary", back_populates="parent_summary")

    def __repr__(self):
        content_preview = self.content[:100] if self.content else "No content"
        return f"<Summary(id={self.id}, content='{content_preview}...')>"
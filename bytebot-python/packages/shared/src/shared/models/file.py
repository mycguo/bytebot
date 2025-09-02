"""File model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class File(Base):
    """File model for task attachments."""
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # MIME type
    size = Column(Integer, nullable=False)  # Size in bytes
    data = Column(Text, nullable=False)  # Base64 encoded file data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="files")

    def __repr__(self):
        size_mb = self.size / (1024 * 1024) if self.size else 0
        return f"<File(id={self.id}, name='{self.name}', type='{self.type}', size={size_mb:.2f}MB)>"
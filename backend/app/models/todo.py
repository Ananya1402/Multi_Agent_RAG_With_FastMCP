"""Todo SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(String(8), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Todo(id={self.id}, title={self.title}, completed={self.completed})>"

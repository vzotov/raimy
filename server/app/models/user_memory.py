from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class UserMemory(Base, TimestampMixin):
    """
    Stores user preferences and profile extracted from conversations.

    Each user has a single memory document that accumulates preferences
    like dietary restrictions, kitchen equipment, cooking skill level, etc.
    """
    __tablename__ = "user_memories"

    user_id = Column(String(255), ForeignKey("users.email"), primary_key=True)
    memory_document = Column(Text, nullable=False, default="")

    # Relationship back to user
    user = relationship("User", back_populates="memory")

    def __repr__(self):
        preview = self.memory_document[:50] + "..." if len(self.memory_document) > 50 else self.memory_document
        return f"<UserMemory(user_id='{self.user_id}', preview='{preview}')>"

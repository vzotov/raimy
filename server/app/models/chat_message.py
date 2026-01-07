from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, TimestampMixin
import uuid

class ChatMessage(Base, TimestampMixin):
    """
    Individual message in a chat session.
    Uses proper timestamp columns from TimestampMixin (created_at, updated_at).
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(JSON, nullable=False)  # Can be string or structured content

    # Relationship
    session = relationship("ChatSession", back_populates="message_records")

    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', session_id='{self.session_id}', role='{self.role}')>"
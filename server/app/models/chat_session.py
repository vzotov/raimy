from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, TimestampMixin
import uuid

class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.email"), nullable=False)
    session_name = Column(String(255), nullable=False, default="Untitled Session")
    session_type = Column(String(50), nullable=False, default="recipe-creator", index=True)
    room_name = Column(String(255), unique=True, nullable=True)  # LiveKit remnant, nullable now
    ingredients = Column(JSON, nullable=True)
    recipe = Column(JSON, nullable=True)  # Work-in-progress recipe data
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True)  # Saved recipe reference

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    message_records = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    saved_recipe = relationship("Recipe", foreign_keys=[recipe_id], overlaps="created_recipes,chat_session")
    created_recipes = relationship("Recipe", foreign_keys="Recipe.chat_session_id", overlaps="saved_recipe,chat_session")

    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}', session_name='{self.session_name}')>"

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, TimestampMixin
import uuid

class MealPlannerSession(Base, TimestampMixin):
    __tablename__ = "meal_planner_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.email"), nullable=False)
    session_name = Column(String(255), nullable=False, default="Untitled Session")
    room_name = Column(String(255), unique=True, nullable=False)

    # Store messages as JSON array: [{"role": "user|assistant", "content": str|dict, "timestamp": str}]
    messages = Column(JSON, default=list)

    # Relationships
    user = relationship("User", back_populates="meal_planner_sessions")

    def __repr__(self):
        return f"<MealPlannerSession(id='{self.id}', user_id='{self.user_id}', session_name='{self.session_name}')>"

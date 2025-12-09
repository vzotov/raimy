from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from .base import Base, TimestampMixin
import uuid

class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    ingredients = Column(JSON, nullable=False, default=list)
    steps = Column(JSON, nullable=False, default=list)
    total_time_minutes = Column(Integer)
    difficulty = Column(String(50))
    servings = Column(Integer)
    tags = Column(ARRAY(String), default=list)

    # Foreign key to user
    user_id = Column(String(255), ForeignKey("users.email"), nullable=False)

    # Foreign key to meal planner session (optional - tracks which conversation created this recipe)
    meal_planner_session_id = Column(UUID(as_uuid=True), ForeignKey("meal_planner_sessions.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="recipes")
    meal_planner_session = relationship("MealPlannerSession", foreign_keys=[meal_planner_session_id])

    def __repr__(self):
        return f"<Recipe(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

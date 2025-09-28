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
    ingredients = Column(ARRAY(String), nullable=False, default=list)
    total_time_minutes = Column(Integer)
    difficulty = Column(String(50))
    servings = Column(Integer)
    tags = Column(ARRAY(String), default=list)

    # Foreign key to user
    user_id = Column(String(255), ForeignKey("users.email"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="recipes")
    steps = relationship("RecipeStep", back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeStep.step_number")

    def __repr__(self):
        return f"<Recipe(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)
    duration_minutes = Column(Integer)
    ingredients = Column(ARRAY(String), default=list)

    # Relationships
    recipe = relationship("Recipe", back_populates="steps")

    def __repr__(self):
        return f"<RecipeStep(id='{self.id}', recipe_id='{self.recipe_id}', step_number={self.step_number})>"
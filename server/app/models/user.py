from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), primary_key=True)
    name = Column(String(255))
    picture = Column(String(500))
    locale = Column(String(10))
    last_login = Column(DateTime(timezone=True))

    # Additional user data stored as JSON
    user_metadata = Column(JSON, default=dict)

    # Relationships
    recipes = relationship("Recipe", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    meal_planner_sessions = relationship("MealPlannerSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"
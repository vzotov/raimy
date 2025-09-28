from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(255), ForeignKey("users.email"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Additional session data stored as JSON
    data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"
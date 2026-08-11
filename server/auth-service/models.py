from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """Service-local view of the shared `users` table — only the columns auth-service needs."""
    __tablename__ = "users"

    email = Column(String(255), primary_key=True)
    name = Column(String(255))
    password_hash = Column(String(255), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)

import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .base import Base


class StepImageCache(Base):
    """Cache of generated step images with vector embeddings for similarity search."""
    __tablename__ = "step_image_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    image_url = Column(Text, nullable=False)
    aspect_ratio = Column(String(20), nullable=False, server_default='1:1')
    prompt_used = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=False)
    generation_time_ms = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, server_default='0')
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

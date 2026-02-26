# Phase 1: Database — pgvector + step_image_cache table

> **Note**: This is the only migration for this entire feature. All other phases use JSON columns (backward-compatible, no migration needed).

## Checklist

- [x] Switch Postgres Docker image to pgvector
- [x] Create migration 008 with step_image_cache table + indexes
- [x] Create StepImageCache SQLAlchemy model
- [x] Update models/__init__.py
- [x] Add pgvector to requirements.txt
- [x] Verify migration runs successfully
- [x] Commit

## Why first

Everything downstream depends on the cache table existing.

## Changes

### 1a. Switch Postgres image — `docker-compose.yml` line 38

Change `image: postgres:15-alpine` to `image: pgvector/pgvector:pg15`. This image includes the pgvector extension pre-installed. Existing data is compatible (same PG15 base). The `postgres_data` volume will persist data across image changes.

### 1b. New migration — `server/alembic/versions/008_add_step_image_cache.py`

Follow the existing migration pattern from `server/alembic/versions/007_add_user_memories.py`:

```python
"""Add step_image_cache table for semantic image caching

Revision ID: 008
Revises: 007
Create Date: 2025-XX-XX
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'step_image_cache',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Column('vector(384)'), nullable=False),  # see note below
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('aspect_ratio', sa.String(20), nullable=False, server_default='1:1'),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Exact match index for fast text lookup
    op.create_index('idx_cache_normalized', 'step_image_cache', ['normalized_text', 'aspect_ratio'])

    # Vector similarity index - use raw SQL for HNSW index since alembic doesn't support it natively
    op.execute('''
        CREATE INDEX idx_cache_embedding ON step_image_cache
        USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)
    ''')


def downgrade() -> None:
    op.drop_table('step_image_cache')
```

**Note on the vector column**: Alembic doesn't natively support pgvector types. For the `embedding` column, use `op.execute()` with raw SQL for the CREATE TABLE, or use the `pgvector.sqlalchemy` Vector type if the migration setup supports it. Look at how the existing migrations in `server/alembic/versions/` handle non-standard types. If pure-alembic doesn't work, use `op.execute()` for the entire CREATE TABLE as raw SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE step_image_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  normalized_text TEXT NOT NULL,
  embedding vector(384) NOT NULL,
  image_url TEXT NOT NULL,
  aspect_ratio TEXT NOT NULL DEFAULT '1:1',
  prompt_used TEXT,
  model_used TEXT NOT NULL,
  generation_time_ms INTEGER,
  usage_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cache_normalized ON step_image_cache(normalized_text, aspect_ratio);
CREATE INDEX idx_cache_embedding ON step_image_cache
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### 1c. New model — `server/app/models/step_image_cache.py`

Follow the pattern from `server/app/models/user_memory.py`. The model uses `Base` and `TimestampMixin` from `server/app/models/base.py`:

```python
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
```

### 1d. Modify — `server/app/models/__init__.py`

Current content:
```python
from .base import Base
from .user import User
from .recipe import Recipe
from .session import Session
from .chat_session import ChatSession
from .chat_message import ChatMessage
from .user_memory import UserMemory

__all__ = ["Base", "User", "Recipe", "Session", "ChatSession", "ChatMessage", "UserMemory"]
```

Add `StepImageCache` import and to `__all__`.

### 1e. Modify — `server/requirements.txt` — add `pgvector` package

## Verification

- `docker compose down && docker compose up -d postgres` (to pick up the new image)
- `docker compose up -d raimy-api` (migrations run on startup via `AUTO_MIGRATE=true`)
- Check logs: `docker compose logs raimy-api | grep -i migrat`
- In pgAdmin (http://localhost:8080): `SELECT * FROM step_image_cache LIMIT 1;` should return empty result without error

## Commit
```
feat: add pgvector and step_image_cache table for semantic image caching
```

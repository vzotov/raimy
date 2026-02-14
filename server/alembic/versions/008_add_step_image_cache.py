"""Add step_image_cache table for semantic image caching

Revision ID: 008
Revises: 007
Create Date: 2026-02-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.execute('''
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
        )
    ''')

    op.execute('''
        CREATE INDEX idx_cache_normalized
        ON step_image_cache(normalized_text, aspect_ratio)
    ''')

    op.execute('''
        CREATE INDEX idx_cache_embedding
        ON step_image_cache USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')


def downgrade() -> None:
    op.drop_table('step_image_cache')

"""Add user_memories table for storing user preferences

Revision ID: 007
Revises: 006
Create Date: 2025-02-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_memories',
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users.email'), primary_key=True),
        sa.Column('memory_document', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('user_memories')

"""Add nutrition column to recipes and recipe_changed to sessions

Revision ID: 004
Revises: 003
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nutrition JSON column to recipes table
    op.add_column('recipes', sa.Column('nutrition', sa.JSON(), nullable=True))
    # Add recipe_changed boolean column to chat_sessions table
    op.add_column('chat_sessions', sa.Column('recipe_changed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('recipes', 'nutrition')
    op.drop_column('chat_sessions', 'recipe_changed')

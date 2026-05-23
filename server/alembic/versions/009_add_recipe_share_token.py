"""Add share_token to recipes for public sharing

Revision ID: 009
Revises: 008
Create Date: 2026-05-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('recipes', sa.Column('share_token', sa.String(36), nullable=True))
    op.create_index('ix_recipes_share_token', 'recipes', ['share_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_recipes_share_token', table_name='recipes')
    op.drop_column('recipes', 'share_token')

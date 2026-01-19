"""Add instacart_link_url cache column to recipes

Revision ID: 003
Revises: 002
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add instacart_link_url column to recipes table
    op.add_column('recipes', sa.Column('instacart_link_url', sa.String(512), nullable=True))


def downgrade() -> None:
    # Remove instacart_link_url column from recipes table
    op.drop_column('recipes', 'instacart_link_url')

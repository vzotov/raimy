"""Add equipment column to recipes

Revision ID: 011
Revises: 010
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add equipment JSON column to recipes table (list of equipment names)
    op.add_column('recipes', sa.Column('equipment', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('recipes', 'equipment')

"""add_ingredients_to_sessions

Revision ID: af116f79365e
Revises: 004
Create Date: 2025-11-26 10:46:52.167000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af116f79365e'
down_revision: Union[str, Sequence[str], None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('meal_planner_sessions',
        sa.Column('ingredients', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('meal_planner_sessions', 'ingredients')

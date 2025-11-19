"""Add meal_planner_session_id to recipes

Revision ID: 004
Revises: 003
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add meal_planner_session_id column to recipes table
    # This allows tracking which conversation created the recipe
    # Nullable because existing recipes and kitchen-created recipes won't have this
    op.add_column(
        'recipes',
        sa.Column(
            'meal_planner_session_id',
            postgresql.UUID(as_uuid=True),
            nullable=True
        )
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_recipes_meal_planner_session',
        'recipes',
        'meal_planner_sessions',
        ['meal_planner_session_id'],
        ['id'],
        ondelete='SET NULL'  # If session is deleted, keep recipe but remove link
    )

    # Create index for faster lookups of recipes by session
    op.create_index(
        'ix_recipes_meal_planner_session_id',
        'recipes',
        ['meal_planner_session_id']
    )


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_recipes_meal_planner_session_id', table_name='recipes')

    # Remove foreign key
    op.drop_constraint('fk_recipes_meal_planner_session', 'recipes', type_='foreignkey')

    # Remove column
    op.drop_column('recipes', 'meal_planner_session_id')

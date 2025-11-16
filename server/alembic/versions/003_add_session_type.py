"""Add session_type to meal_planner_sessions

Revision ID: 003
Revises: 002
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add session_type column with default value
    op.add_column(
        'meal_planner_sessions',
        sa.Column('session_type', sa.String(length=50), nullable=False, server_default='meal-planner')
    )

    # Make room_name nullable (LiveKit remnant, will be removed in future migration)
    op.alter_column(
        'meal_planner_sessions',
        'room_name',
        existing_type=sa.String(),
        nullable=True
    )

    # Create index on session_type for faster filtering
    op.create_index(
        'ix_meal_planner_sessions_session_type',
        'meal_planner_sessions',
        ['session_type']
    )


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_meal_planner_sessions_session_type', table_name='meal_planner_sessions')

    # Make room_name non-nullable again
    op.alter_column(
        'meal_planner_sessions',
        'room_name',
        existing_type=sa.String(),
        nullable=False
    )

    # Remove session_type column
    op.drop_column('meal_planner_sessions', 'session_type')

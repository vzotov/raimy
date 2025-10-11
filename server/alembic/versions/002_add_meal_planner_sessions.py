"""Add meal_planner_sessions table

Revision ID: 002
Revises: 001
Create Date: 2025-10-11 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create meal_planner_sessions table
    op.create_table('meal_planner_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('session_name', sa.String(length=255), nullable=False, server_default='Untitled Session'),
        sa.Column('room_name', sa.String(length=255), nullable=False),
        sa.Column('messages', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.email'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_name')
    )

    # Create indexes for better performance
    op.create_index('ix_meal_planner_sessions_user_id', 'meal_planner_sessions', ['user_id'])
    op.create_index('ix_meal_planner_sessions_room_name', 'meal_planner_sessions', ['room_name'])


def downgrade() -> None:
    op.drop_index('ix_meal_planner_sessions_room_name', table_name='meal_planner_sessions')
    op.drop_index('ix_meal_planner_sessions_user_id', table_name='meal_planner_sessions')
    op.drop_table('meal_planner_sessions')

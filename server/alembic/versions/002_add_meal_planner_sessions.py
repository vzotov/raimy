"""Add meal_planner_sessions and meal_planner_messages tables

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
    # Create meal_planner_sessions table with all columns
    op.create_table('meal_planner_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('session_name', sa.String(length=255), nullable=False, server_default='Untitled Session'),
        sa.Column('session_type', sa.String(length=50), nullable=False, server_default='meal-planner'),
        sa.Column('room_name', sa.String(length=255), nullable=True),
        sa.Column('ingredients', sa.JSON(), nullable=True),
        sa.Column('recipe', sa.JSON(), nullable=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.email'], ),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_name')
    )

    # Create indexes for better performance
    op.create_index('ix_meal_planner_sessions_user_id', 'meal_planner_sessions', ['user_id'])
    op.create_index('ix_meal_planner_sessions_room_name', 'meal_planner_sessions', ['room_name'])
    op.create_index('ix_meal_planner_sessions_session_type', 'meal_planner_sessions', ['session_type'])

    # Create meal_planner_messages table
    op.create_table('meal_planner_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['meal_planner_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for messages table
    op.create_index('ix_meal_planner_messages_session_id', 'meal_planner_messages', ['session_id'])
    op.create_index('ix_meal_planner_messages_created_at', 'meal_planner_messages', ['created_at'])

    # Add meal_planner_session_id to recipes table (link recipe to the session that created it)
    op.add_column('recipes', sa.Column('meal_planner_session_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_recipes_meal_planner_session', 'recipes', 'meal_planner_sessions',
                         ['meal_planner_session_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_recipes_meal_planner_session_id', 'recipes', ['meal_planner_session_id'])


def downgrade() -> None:
    # Drop recipe link from recipes table
    op.drop_index('ix_recipes_meal_planner_session_id', table_name='recipes')
    op.drop_constraint('fk_recipes_meal_planner_session', 'recipes', type_='foreignkey')
    op.drop_column('recipes', 'meal_planner_session_id')

    # Drop messages table first (due to FK constraint)
    op.drop_index('ix_meal_planner_messages_created_at', table_name='meal_planner_messages')
    op.drop_index('ix_meal_planner_messages_session_id', table_name='meal_planner_messages')
    op.drop_table('meal_planner_messages')

    # Drop sessions table
    op.drop_index('ix_meal_planner_sessions_session_type', table_name='meal_planner_sessions')
    op.drop_index('ix_meal_planner_sessions_room_name', table_name='meal_planner_sessions')
    op.drop_index('ix_meal_planner_sessions_user_id', table_name='meal_planner_sessions')
    op.drop_table('meal_planner_sessions')

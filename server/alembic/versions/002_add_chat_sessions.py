"""Add chat_sessions and chat_messages tables

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
    # Create chat_sessions table with all columns
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('session_name', sa.String(length=255), nullable=False, server_default='Untitled Session'),
        sa.Column('session_type', sa.String(length=50), nullable=False, server_default='recipe-creator'),
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
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_room_name', 'chat_sessions', ['room_name'])
    op.create_index('ix_chat_sessions_session_type', 'chat_sessions', ['session_type'])

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for messages table
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])

    # Add chat_session_id to recipes table (link recipe to the session that created it)
    op.add_column('recipes', sa.Column('chat_session_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_recipes_chat_session', 'recipes', 'chat_sessions',
                         ['chat_session_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_recipes_chat_session_id', 'recipes', ['chat_session_id'])


def downgrade() -> None:
    # Drop recipe link from recipes table
    op.drop_index('ix_recipes_chat_session_id', table_name='recipes')
    op.drop_constraint('fk_recipes_chat_session', 'recipes', type_='foreignkey')
    op.drop_column('recipes', 'chat_session_id')

    # Drop messages table first (due to FK constraint)
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')

    # Drop sessions table
    op.drop_index('ix_chat_sessions_session_type', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_room_name', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')

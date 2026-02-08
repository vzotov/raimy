"""Add user_memories table and finished column to chat_sessions

Revision ID: 007
Revises: 006
Create Date: 2025-02-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_memories table
    op.create_table(
        'user_memories',
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users.email'), primary_key=True),
        sa.Column('memory_document', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Add finished column to chat_sessions
    op.add_column(
        'chat_sessions',
        sa.Column('finished', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('chat_sessions', 'finished')
    op.drop_table('user_memories')

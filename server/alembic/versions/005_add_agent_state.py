"""Add agent_state column to chat_sessions

Revision ID: 005
Revises: 004
Create Date: 2025-01-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add agent_state JSON column to chat_sessions table
    # Used by kitchen agent to track current step, completed steps, etc.
    op.add_column('chat_sessions', sa.Column('agent_state', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_sessions', 'agent_state')

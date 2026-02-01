"""Increase user picture column size

Revision ID: 006
Revises: 005
Create Date: 2025-02-01

Google OAuth can return profile picture URLs longer than 500 characters,
causing user save to fail and subsequently blocking session creation.

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change picture column from VARCHAR(500) to TEXT to accommodate long Google OAuth URLs
    op.alter_column('users', 'picture',
                    existing_type=sa.String(500),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'picture',
                    existing_type=sa.Text(),
                    type_=sa.String(500),
                    existing_nullable=True)

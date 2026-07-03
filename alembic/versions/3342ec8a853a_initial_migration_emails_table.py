"""Initial migration: emails table

Revision ID: 3342ec8a853a
Revises: 
Create Date: 2026-05-13 12:50:04.530311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3342ec8a853a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('emails')
"""alter_balance_replace_quantity_by_reserved_and_available

Revision ID: a3f5d9114e2b
Revises: 8c7376ee8e98
Create Date: 2025-04-05 22:02:32.145091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f5d9114e2b'
down_revision: Union[str, None] = '8c7376ee8e98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users_balance', sa.Column('available', sa.Integer(), nullable=False))
    op.add_column('users_balance', sa.Column('reserved', sa.Integer(), nullable=False))
    op.drop_column('users_balance', 'quantity')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users_balance', sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('users_balance', 'reserved')
    op.drop_column('users_balance', 'available')

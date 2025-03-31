"""recreate_balances_and_instrument_table

Revision ID: a7d2cf91f6ac
Revises: da671b6cc4e1
Create Date: 2025-03-31 18:05:35.624063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7d2cf91f6ac'
down_revision: Union[str, None] = 'da671b6cc4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('instruments',
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('ticker', name=op.f('pk_instruments')),
    sa.UniqueConstraint('name', name=op.f('uq_instruments_name'))
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('instruments')

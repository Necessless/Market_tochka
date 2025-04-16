"""create_transactions_table

Revision ID: 8c7376ee8e98
Revises: 4e3c0359c425
Create Date: 2025-04-03 16:45:57.083767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8c7376ee8e98'
down_revision: Union[str, None] = '4e3c0359c425'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('instruments_transactions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_instruments_transactions_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_instruments_transactions'))
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('instruments_transactions')


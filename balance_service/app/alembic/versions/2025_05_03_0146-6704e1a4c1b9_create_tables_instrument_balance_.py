"""Create tables instrument balance transaction

Revision ID: 6704e1a4c1b9
Revises: 
Create Date: 2025-05-03 01:46:51.799093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6704e1a4c1b9'
down_revision: Union[str, None] = None
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
    op.create_table('instruments_transactions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_instruments_transactions_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_instruments_transactions'))
    )
    op.create_table('users_balance',
    sa.Column('user_name', sa.String(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('available', sa.Integer(), nullable=False),
    sa.Column('reserved', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_users_balance_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_name', 'instrument_ticker', name=op.f('pk_users_balance'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users_balance')
    op.drop_table('instruments_transactions')
    op.drop_table('instruments')

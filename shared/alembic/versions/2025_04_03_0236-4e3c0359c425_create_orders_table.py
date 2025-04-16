"""create_orders_table

Revision ID: 4e3c0359c425
Revises: 1333e1efc004
Create Date: 2025-04-03 02:36:03.166122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '4e3c0359c425'
down_revision: Union[str, None] = '1333e1efc004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('orders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('order_type', sa.Enum('MARKET', 'LIMIT', name='order_type'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('direction', sa.Enum('BUY', 'SELL', name='direction'), nullable=False),
    sa.Column('status', sa.Enum('NEW', 'EXECUTED', 'PARTIALLY_EXECUTED', 'CANCELLED', name='orderstatus'), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('filled', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_orders_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name=op.f('fk_orders_user_id_Users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_orders'))
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('orders')

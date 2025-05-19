"""create orders table

Revision ID: b49fcdd00cfd
Revises: 
Create Date: 2025-05-18 23:13:00.079979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b49fcdd00cfd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('orders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('NEW', 'EXECUTED', 'PARTIALLY_EXECUTED', 'CANCELLED', name='orderstatus'), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('direction', sa.Enum('BUY', 'SELL', name='direction'), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('filled', sa.Integer(), nullable=False),
    sa.Column('order_type', sa.Enum('MARKET', 'LIMIT', name='order_type'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_orders'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('orders')


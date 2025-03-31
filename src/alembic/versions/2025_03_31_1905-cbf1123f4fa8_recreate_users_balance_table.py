"""recreate_users_balance_table

Revision ID: cbf1123f4fa8
Revises: a7d2cf91f6ac
Create Date: 2025-03-31 19:05:30.391953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'cbf1123f4fa8'
down_revision: Union[str, None] = 'a7d2cf91f6ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users_balance',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_users_balance_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name=op.f('fk_users_balance_user_id_Users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'instrument_ticker', name=op.f('pk_users_balance'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users_balance')


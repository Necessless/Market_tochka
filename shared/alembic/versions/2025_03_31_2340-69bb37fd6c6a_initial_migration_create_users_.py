"""initial_migration_create_users_instruments_balance_tables

Revision ID: 69bb37fd6c6a
Revises: 851404e70001
Create Date: 2025-03-31 23:40:36.082187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '69bb37fd6c6a'
down_revision: Union[str, None] = '851404e70001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('Users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('USER', 'ADMIN', name='authrole'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Users')),
    sa.UniqueConstraint('name', name=op.f('uq_Users_name'))
    )
    op.create_table('instruments',
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('ticker', name=op.f('pk_instruments')),
    sa.UniqueConstraint('name', name=op.f('uq_instruments_name'))
    )
    op.create_table('users_balance',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('instrument_ticker', sa.String(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_ticker'], ['instruments.ticker'], name=op.f('fk_users_balance_instrument_ticker_instruments'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name=op.f('fk_users_balance_user_id_Users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'instrument_ticker', name=op.f('pk_users_balance'))
    )



def downgrade() -> None:
    op.drop_table('users_balance')
    op.drop_table('instruments')
    op.drop_table('Users')


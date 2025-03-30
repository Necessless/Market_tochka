"""create_instruments_and_balances_table_as_secondary

Revision ID: f6aefceb6564
Revises: 0be9b9de76bf
Create Date: 2025-03-29 12:41:10.296149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6aefceb6564'
down_revision: Union[str, None] = '0be9b9de76bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users_balances',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('instrument_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], name=op.f('fk_users_balances_instrument_id_instruments')),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name=op.f('fk_users_balances_user_id_Users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users_balances'))
    )
    op.drop_constraint('fk_user_wallets_user_id_Users','user_wallets')
    op.drop_constraint('fk_wallets_to_instruments_instrument_id_instruments','wallets_to_instruments')
    op.drop_constraint('fk_wallets_to_instruments_wallet_id_user_wallets','wallets_to_instruments')
    op.drop_table('user_wallets')   
    op.drop_table('wallets_to_instruments')



def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('wallets_to_instruments',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('wallet_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('instrument_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], name='fk_wallets_to_instruments_instrument_id_instruments'),
    sa.ForeignKeyConstraint(['wallet_id'], ['user_wallets.id'], name='fk_wallets_to_instruments_wallet_id_user_wallets'),
    sa.PrimaryKeyConstraint('id', name='pk_wallets_to_instruments')
    )
    op.create_table('user_wallets',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name='fk_user_wallets_user_id_Users'),
    sa.PrimaryKeyConstraint('id', name='pk_user_wallets')
    )
    op.drop_table('users_balances')


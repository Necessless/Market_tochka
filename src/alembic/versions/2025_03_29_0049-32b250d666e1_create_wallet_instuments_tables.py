"""create_wallet_instuments_tables

Revision ID: 32b250d666e1
Revises: 4abc48e21f76
Create Date: 2025-03-29 00:49:46.230939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '32b250d666e1'
down_revision: Union[str, None] = '4abc48e21f76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('instruments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_instruments')),
    sa.UniqueConstraint('name', name=op.f('uq_instruments_name')),
    sa.UniqueConstraint('ticker', name=op.f('uq_instruments_ticker'))
    )
    op.create_table('user_wallets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], name=op.f('fk_user_wallets_user_id_Users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_wallets'))
    )
    op.create_table('wallets_to_instruments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('wallet_id', sa.UUID(), nullable=False),
    sa.Column('instrument_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], name=op.f('fk_wallets_to_instruments_instrument_id_instruments')),
    sa.ForeignKeyConstraint(['wallet_id'], ['user_wallets.id'], name=op.f('fk_wallets_to_instruments_wallet_id_user_wallets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wallets_to_instruments'))
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('wallets_to_instruments')
    op.drop_table('user_wallets')
    op.drop_table('instruments')


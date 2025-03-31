"""alter_instruments_ticker_is_pk

Revision ID: da671b6cc4e1
Revises: dd84f9e67b02
Create Date: 2025-03-31 17:46:59.446100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'da671b6cc4e1'
down_revision: Union[str, None] = 'dd84f9e67b02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('users_balances')



def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('users_balances',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('instrument_id', sa.UUID(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users_balances'))
    )
    op.create_foreign_key(op.f('fk_users_balances_user_id_Users'), 'users_balances', 'Users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_users_balances_instrument_id_instruments'), 'users_balances', 'instruments', ['instrument_id'], ['id'], ondelete='CASCADE')
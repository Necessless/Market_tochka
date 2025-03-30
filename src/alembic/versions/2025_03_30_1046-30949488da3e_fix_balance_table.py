"""fix_balance_table

Revision ID: 30949488da3e
Revises: e20b8151677a
Create Date: 2025-03-30 10:46:19.371519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '30949488da3e'
down_revision: Union[str, None] = 'e20b8151677a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('fk_users_balances_user_id_Users', 'users_balances', type_='foreignkey')
    op.drop_constraint('fk_users_balances_instrument_id_instruments', 'users_balances', type_='foreignkey')
    op.create_foreign_key(op.f('fk_users_balances_user_id_Users'), 'users_balances', 'Users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_users_balances_instrument_id_instruments'), 'users_balances', 'instruments', ['instrument_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('fk_users_balances_instrument_id_instruments'), 'users_balances', type_='foreignkey')
    op.drop_constraint(op.f('fk_users_balances_user_id_Users'), 'users_balances', type_='foreignkey')
    op.create_foreign_key('fk_users_balances_instrument_id_instruments', 'users_balances', 'instruments', ['instrument_id'], ['id'])
    op.create_foreign_key('fk_users_balances_user_id_Users', 'users_balances', 'Users', ['user_id'], ['id'])


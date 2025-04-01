"""replace_user_id_by_user_name_In_balance

Revision ID: 1333e1efc004
Revises: 69bb37fd6c6a
Create Date: 2025-04-01 23:01:17.042335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1333e1efc004'
down_revision: Union[str, None] = '69bb37fd6c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users_balance', sa.Column('user_name', sa.String(), nullable=False))
    op.drop_constraint('fk_users_balance_user_id_Users', 'users_balance', type_='foreignkey')
    op.create_foreign_key(op.f('fk_users_balance_user_name_Users'), 'users_balance', 'Users', ['user_name'], ['name'], ondelete='CASCADE')
    op.drop_column('users_balance', 'user_id')
    op.create_primary_key(op.f('pk_users_balance'), 'users_balance', ['user_name', 'instrument_ticker'])


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users_balance', sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(op.f('fk_users_balance_user_name_Users'), 'users_balance', type_='foreignkey')
    op.create_foreign_key('fk_users_balance_user_id_Users', 'users_balance', 'Users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_column('users_balance', 'user_name')
    op.drop_constraint(op.f('pk_users_balance'), 'users_balance', type_='primary')

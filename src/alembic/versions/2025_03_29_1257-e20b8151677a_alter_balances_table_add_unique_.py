"""alter_balances_table_add_unique_constraint

Revision ID: e20b8151677a
Revises: f6aefceb6564
Create Date: 2025-03-29 12:57:16.311527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e20b8151677a'
down_revision: Union[str, None] = 'f6aefceb6564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_user_instrument', 'users_balances', ['user_id', 'instrument_id'])



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_user_instrument', 'users_balances', type_='unique')

"""alter_balances_instrument_id_can_be_null

Revision ID: dd84f9e67b02
Revises: 30949488da3e
Create Date: 2025-03-30 21:47:10.359733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dd84f9e67b02'
down_revision: Union[str, None] = '30949488da3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users_balances', 'instrument_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users_balances', 'instrument_id',
               existing_type=sa.UUID(),
               nullable=False)


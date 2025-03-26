"""id_from_int_to_str

Revision ID: f5bdaa28d3c2
Revises: f86e98dff915
Create Date: 2025-03-26 23:28:49.710669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5bdaa28d3c2'
down_revision: Union[str, None] = 'f86e98dff915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Users', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Users', 'id',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)


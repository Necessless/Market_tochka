"""user_name is no longer unique

Revision ID: 4408122e6dec
Revises: 6e6b7fdb9f2b
Create Date: 2025-05-14 17:51:38.684451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4408122e6dec'
down_revision: Union[str, None] = '6e6b7fdb9f2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('uq_Users_name', 'Users', type_='unique')



def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint('uq_Users_name', 'Users', ['name'])

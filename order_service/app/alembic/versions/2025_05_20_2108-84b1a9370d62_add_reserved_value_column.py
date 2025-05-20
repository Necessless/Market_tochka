"""Add reserved_value column

Revision ID: 84b1a9370d62
Revises: b49fcdd00cfd
Create Date: 2025-05-20 21:08:15.321302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84b1a9370d62'
down_revision: Union[str, None] = 'b49fcdd00cfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('reserved_value', sa.Integer(), nullable=False))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'reserved_value')

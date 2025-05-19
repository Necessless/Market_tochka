"""user_id constraint

Revision ID: d451bcf08f6f
Revises: eb607d9800f1
Create Date: 2025-05-16 15:59:21.855077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd451bcf08f6f'
down_revision: Union[str, None] = 'eb607d9800f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('user_ticker_constraint', 'users_balance', ['user_id', 'instrument_ticker'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('user_ticker_constraint', 'users_balance', type_='unique')

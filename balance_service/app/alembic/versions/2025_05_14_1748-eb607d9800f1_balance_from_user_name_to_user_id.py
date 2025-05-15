"""balance from user_name to user_Id

Revision ID: eb607d9800f1
Revises: 6704e1a4c1b9
Create Date: 2025-05-14 17:48:03.669290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'eb607d9800f1'
down_revision: Union[str, None] = '6704e1a4c1b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users_balance', sa.Column('user_id', sa.UUID(), nullable=False))
    op.drop_column('users_balance', 'user_name')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users_balance', sa.Column('user_name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('users_balance', 'user_id')


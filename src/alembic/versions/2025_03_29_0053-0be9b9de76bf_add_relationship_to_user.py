"""add_relationship_to_user

Revision ID: 0be9b9de76bf
Revises: 32b250d666e1
Create Date: 2025-03-29 00:53:33.962184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0be9b9de76bf'
down_revision: Union[str, None] = '32b250d666e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass

def downgrade() -> None:
    """Downgrade schema."""
    pass

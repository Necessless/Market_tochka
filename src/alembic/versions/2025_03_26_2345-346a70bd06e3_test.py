"""test

Revision ID: 346a70bd06e3
Revises: f8f6c87a2789
Create Date: 2025-03-26 23:45:08.837374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '346a70bd06e3'
down_revision: Union[str, None] = 'f8f6c87a2789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass


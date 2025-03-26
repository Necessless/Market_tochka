"""create_users_table

Revision ID: f86e98dff915
Revises: 4ed093ecc93d
Create Date: 2025-03-26 12:12:24.396575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f86e98dff915'
down_revision: Union[str, None] = '4ed093ecc93d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('USER', 'ADMIN', name='authrole'), nullable=False),
    sa.Column('api_key', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Users')),
    sa.UniqueConstraint('api_key', name=op.f('uq_Users_api_key')),
    sa.UniqueConstraint('name', name=op.f('uq_Users_name'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('Users')

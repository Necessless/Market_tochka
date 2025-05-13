"""create table users

Revision ID: 6e6b7fdb9f2b
Revises: 
Create Date: 2025-05-09 01:42:20.900341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '6e6b7fdb9f2b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('USER', 'ADMIN', name='authrole'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Users')),
    sa.UniqueConstraint('name', name=op.f('uq_Users_name'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('Users')


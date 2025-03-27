"""create_table_users

Revision ID: 4abc48e21f76
Revises: 
Create Date: 2025-03-27 12:26:22.234934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4abc48e21f76'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Users',
    sa.Column('id', sa.UUID(), nullable=False),
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

"""id_from_int_to_str

Revision ID: f8f6c87a2789
Revises: f5bdaa28d3c2
Create Date: 2025-03-26 23:42:58.297164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'f8f6c87a2789'
down_revision: Union[str, None] = 'f5bdaa28d3c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Users', 'id',
               existing_type=sa.VARCHAR(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('nextval(\'"Users_id_seq"\'::regclass)'))



def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Users', 'id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('nextval(\'"Users_id_seq"\'::regclass)'))

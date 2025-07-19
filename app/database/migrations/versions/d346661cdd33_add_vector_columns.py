"""Add vector columns

Revision ID: d346661cdd33
Revises: b991d1765476
Create Date: 2025-07-19 09:07:37.934202
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

from app.database.types import Vector


# revision identifiers, used by Alembic.
revision: str = 'd346661cdd33'
down_revision: Union[str, None] = 'b991d1765476'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.add_column('cities', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('places', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('activities', sa.Column('embedding', Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'embedding')
    op.drop_column('cities', 'embedding')
    op.drop_column('places', 'embedding')

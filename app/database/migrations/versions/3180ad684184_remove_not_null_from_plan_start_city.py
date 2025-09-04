"""remove not null from plan start city

Revision ID: 3180ad684184
Revises: 82ee810c101c
Create Date: 2025-08-29 13:27:56.627175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3180ad684184'
down_revision: Union[str, None] = '82ee810c101c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('plans', 'start_city_id', nullable=True)


def downgrade() -> None:
    pass

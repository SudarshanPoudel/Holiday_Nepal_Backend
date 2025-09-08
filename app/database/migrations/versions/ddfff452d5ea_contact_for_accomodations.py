"""contact for accomodations

Revision ID: ddfff452d5ea
Revises: 3180ad684184
Create Date: 2025-09-08 12:57:08.849890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddfff452d5ea'
down_revision: Union[str, None] = '3180ad684184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accommodation_services', sa.Column('contact', sa.String(), nullable=True))
    op.add_column('transport_services', sa.Column('contact', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('transport_services', 'contact')
    op.drop_column('accommodation_services', 'contact')

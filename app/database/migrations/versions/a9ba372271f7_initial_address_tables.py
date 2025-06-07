"""initial address tables

Revision ID: a9ba372271f7
Revises: 
Create Date: 2025-04-10 06:53:51.589937
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9ba372271f7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'districts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, index=True, nullable=False),
        sa.Column('headquarter', sa.String, nullable=True)
    )

    op.create_table(
        'municipalities',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, index=True, nullable=False),
        sa.Column('district_id', sa.Integer, sa.ForeignKey('districts.id'), index=True, nullable=False),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('latitude', sa.Float, nullable=True)
    )


def downgrade() -> None:
    op.drop_table('municipalities')
    op.drop_table('districts')

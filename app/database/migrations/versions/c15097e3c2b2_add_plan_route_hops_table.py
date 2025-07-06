"""Add plan route hops table

Revision ID: c15097e3c2b2
Revises: 45b73d05f1a8
Create Date: 2025-07-04 17:31:42.937360
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c15097e3c2b2'
down_revision: Union[str, None] = '45b73d05f1a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plan_route_hops',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('plan_day_step_id', sa.Integer(), sa.ForeignKey('plan_day_steps.id', ondelete="CASCADE"), nullable=False),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('transport_routes.id', ondelete="CASCADE"), nullable=False),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.Column('destination_municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id', ondelete="CASCADE"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('plan_route_hops')

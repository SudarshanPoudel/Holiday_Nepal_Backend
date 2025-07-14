"""Drop time frame column from plans

Revision ID: b991d1765476
Revises: 82ee810c101c
Create Date: 2025-07-14 08:50:03.931977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b991d1765476'
down_revision: Union[str, None] = '82ee810c101c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enums
plan_day_time_frame_enum = sa.Enum(
    'morning', 'afternoon', 'evening', 'night', 'full_day',
    name='plandaytimeframeenum'
)

def upgrade() -> None:
    op.drop_column('plan_day_steps', 'time_frame')
    plan_day_time_frame_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.add_column('plan_day_steps', sa.Column('time_frame', plan_day_time_frame_enum, nullable=True))

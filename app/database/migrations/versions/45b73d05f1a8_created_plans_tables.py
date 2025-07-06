"""Created plans tables

Revision ID: 45b73d05f1a8
Revises: 8820514ef02f
Create Date: 2025-06-14 12:22:17.809105
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '45b73d05f1a8'
down_revision: Union[str, None] = '8820514ef02f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enums
plan_day_time_frame_enum = sa.Enum(
    'morning', 'afternoon', 'evening', 'night', 'full day',
    name='plandaytimeframeenum'
)
plan_day_step_category_enum = sa.Enum(
    'visit', 'activity', 'transport',
    name='plandaystepcategoryenum'
)

def upgrade() -> None:
    # plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('no_of_days', sa.Integer(), nullable=False),
        sa.Column('no_of_people', sa.Integer(), nullable=False),
        sa.Column('min_budget', sa.Float(), nullable=False),
        sa.Column('max_budget', sa.Float(), nullable=True),
        sa.Column('min_travel_distance', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('vote_count', sa.Integer(), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('start_municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=False),
        sa.Column('end_municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # plan_days table
    op.create_table(
        'plan_days',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('index', sa.Integer(), nullable=False),  # was 'day' before
        sa.Column('title', sa.String(), nullable=False)
    )

    # plan_day_steps table
    op.create_table(
        'plan_day_steps',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.Column('plan_day_id', sa.Integer(), sa.ForeignKey('plan_days.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('category', plan_day_step_category_enum, nullable=True),
        sa.Column('time_frame', plan_day_time_frame_enum, nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id'), nullable=True),
        sa.Column('place_id', sa.Integer(), sa.ForeignKey('places.id'), nullable=True),
        sa.Column('place_activity_id', sa.Integer(), sa.ForeignKey('place_activities.id'), nullable=True),
        sa.Column('start_municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=True),
        sa.Column('end_municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=True)
    )

    # plan_day_step_activities association table
    op.create_table(
        'plan_day_step_activities',
        sa.Column('plan_day_step_id', sa.Integer(), sa.ForeignKey('plan_day_steps.id'), primary_key=True),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), primary_key=True)
    )


def downgrade() -> None:
    op.drop_table('plan_day_step_activities')
    op.drop_table('plan_day_steps')
    op.drop_table('plan_days')
    op.drop_table('plans')
    plan_day_time_frame_enum.drop(op.get_bind(), checkfirst=True)
    plan_day_step_category_enum.drop(op.get_bind(), checkfirst=True)

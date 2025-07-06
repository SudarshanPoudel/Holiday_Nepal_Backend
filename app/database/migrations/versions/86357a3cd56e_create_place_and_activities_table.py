"""create place and activities table

Revision ID: 86357a3cd56e
Revises: 745fabbe5f24
Create Date: 2025-05-31 13:04:36.283583
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86357a3cd56e'
down_revision: Union[str, None] = '745fabbe5f24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    place_category_enum = sa.Enum(
        'natural', 'cultural', 'historic', 'religious', 'adventure', 'wildlife', 'educational', 'architectural', 'other',
        name='placecategoryenum'
    )

    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('name_slug', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id'), nullable=True),
    )

    # Create places table
    op.create_table(
        'places',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), index=True, nullable=False),
        sa.Column('category', place_category_enum, nullable=True),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=False),
        sa.Column('average_visit_duration', sa.Float(), nullable=True),
        sa.Column('average_visit_cost', sa.Float(), nullable=True),
    )

    # Create place_activities association table
    op.create_table(
        'place_activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('place_id', sa.Integer(), sa.ForeignKey('places.id'), index=True, nullable=False),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), index=True, nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('average_duration', sa.Float(), nullable=True),
        sa.Column('average_cost', sa.Float(), nullable=True),
    )

    # Create place_images association tabless
    op.create_table(
        'place_images',
        sa.Column('place_id', sa.Integer(), sa.ForeignKey('places.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id', ondelete="CASCADE"), primary_key=True)
    )


def downgrade() -> None:
    op.drop_table('place_images')
    op.drop_table('place_activities')
    op.drop_table('places')
    op.drop_table('activities')
    op.execute('DROP TYPE placecategoryenum')
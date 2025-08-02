"""Created accommodation service table

Revision ID: 8820514ef02f
Revises: 4951bfa9ccb5
Create Date: 2025-06-11 12:59:22.327785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8820514ef02f'
down_revision: Union[str, None] = '4951bfa9ccb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    accommodation_category_enum = sa.Enum(
        'hotel', 'motel', 'resort', 'hostel', 'homestay', 'other',
        name='accommodationcategoryenum'
    )

    op.create_table(
        'accommodation_services',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('city_id', sa.Integer(), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('full_address', sa.String(), nullable=False),
        sa.Column('accommodation_category', accommodation_category_enum, nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('cost_per_night', sa.Float(), nullable=False),
    )
    
    op.create_table(
        'accommodation_service_images',
        sa.Column('accommodation_service_id', sa.Integer(), sa.ForeignKey('accommodation_services.id'), primary_key=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('accommodation_service_images')
    op.drop_table('accommodation_services')
    op.execute('DROP TYPE IF EXISTS accommodationcategoryenum')

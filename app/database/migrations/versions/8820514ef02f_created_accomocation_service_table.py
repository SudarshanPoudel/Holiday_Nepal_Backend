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
    accomodation_category_enum = sa.Enum(
        'hotel', 'motel', 'resort', 'hostel', 'homestay', 'other',
        name='accomodationcategoryenum'
    )

    op.create_table(
        'accomodation_services',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('service_provider_id', sa.Integer(), sa.ForeignKey('service_providers.id'), nullable=True),
        sa.Column('municipality_id', sa.Integer(), sa.ForeignKey('municipalities.id'), nullable=False),
        sa.Column('full_location', sa.String(), nullable=False),
        sa.Column('accomodation_category', accomodation_category_enum, nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('cost_per_night', sa.Float(), nullable=False),
    )
    op.create_table(
        'accomodation_service_images',
        sa.Column('accomodation_service_id', sa.Integer(), sa.ForeignKey('accomodation_services.id'), primary_key=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('accomodation_service_images')
    op.drop_table('accomodation_services')
    op.execute('DROP TYPE IF EXISTS accomodationcategoryenum')

"""Add transport tables

Revision ID: 4951bfa9ccb5
Revises: 86357a3cd56e
Create Date: 2025-06-04 12:07:34.783276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4951bfa9ccb5'
down_revision: Union[str, None] = '86357a3cd56e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum types
    route_category_enum = sa.Enum(
        'walking', 'road', 'air',
        name='routecategoryenum'
    )

    transport_category_enum = sa.Enum(
        'bus', 'taxi', 'bike', 'minibus', 'plane', 'helicopter', 'other',
        name='transportcategoryenum'
    )

    # Create tables
    op.create_table(
        'transport_routes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('start_city_id', sa.Integer(), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('end_city_id', sa.Integer(), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('route_category', route_category_enum, nullable=False),
        sa.Column('distance', sa.Float(), nullable=False),
        sa.Column('average_duration', sa.Float(), nullable=False),
        sa.Column('average_cost', sa.Float(), nullable=False)
    )

    op.create_table(
        'transport_services',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('start_city_id', sa.Integer(), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('end_city_id', sa.Integer(), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('route_category', route_category_enum, nullable=False),
        sa.Column('transport_category', transport_category_enum, nullable=False),
        sa.Column('average_duration', sa.Float(), nullable=True),
        sa.Column('distance', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=True)
    )

    op.create_table(
        'transport_service_route_segments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('transport_services.id'), nullable=False),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('transport_routes.id'), nullable=False),
        sa.Column('index', sa.Integer(), nullable=False)
    )

    op.create_table(
        'transport_service_images',
        sa.Column('transport_service_id', sa.Integer(), sa.ForeignKey('transport_services.id'), primary_key=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('images.id'), primary_key=True)
    )


def downgrade() -> None:
    op.drop_table('transport_service_images')
    op.drop_table('transport_service_route_segments')
    op.drop_table('transport_services')
    op.drop_table('transport_routes')
    op.execute('DROP TYPE routecategoryenum')
    op.execute('DROP TYPE transportcategoryenum')

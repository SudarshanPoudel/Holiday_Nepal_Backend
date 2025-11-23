"""Create users table with constraints and indexes

Revision ID: 123456789abc
Revises: a9ba372271f7 
Create Date: 2025-05-02 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = '123456789abc'
down_revision: Union[str, None] = 'a9ba372271f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum type for image category
    image_category_enum = sa.Enum(
        'place', 'activity', 'services', 'user_profile', 'other',
        name='imagecategoryenum'
    )


    op.create_table(
        'images',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key', sa.String, unique=True, index=True, nullable=False),
        sa.Column('category', image_category_enum, nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("username", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id"), nullable=True, index=True),
        sa.Column("prefer_place_categories", JSONB(), nullable=True),  # EnumList stored as JSON
        sa.Column("prefer_travel_distance", sa.Enum("short", "medium", "long", name="distancepreferenceenum"), nullable=True),
        sa.Column("additional_preferences", sa.String(), nullable=True),
        sa.Column("image_id", sa.Integer(), sa.ForeignKey("images.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )



def downgrade() -> None:
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS distancepreferenceenum")
    op.drop_table("images")
    op.execute("DROP TYPE IF EXISTS imagecategoryenum")
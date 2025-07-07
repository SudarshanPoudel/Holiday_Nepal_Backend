"""initial address tables

Revision ID: a9ba372271f7
Revises: 
Create Date: 2025-04-10 06:53:51.589937
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = 'a9ba372271f7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create 'cities' table
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, index=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("location", Geography(geometry_type='POINT', srid=4326), nullable=True)
    )

    # Optional: Add GIST index for spatial queries
    op.execute("CREATE INDEX cities_location_idx ON cities USING GIST (location)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS cities_location_idx")
    op.drop_table("cities")
    op.execute("DROP EXTENSION IF EXISTS postgis")
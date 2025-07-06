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


def upgrade():
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.add_column("cities", sa.Column("location", sa.types.UserDefinedType(), nullable=True))
    op.execute("""
        UPDATE cities
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
        WHERE longitude IS NOT NULL AND latitude IS NOT NULL
    """)
    op.execute("CREATE INDEX cities_location_idx ON cities USING GIST (location)")

def downgrade():
    op.drop_index("cities_location_idx", table_name="cities")
    op.drop_column("cities", "location")
    op.execute("DROP EXTENSION IF EXISTS postgis")
from sqlalchemy import text
from app.core.repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Params

from app.modules.cities.models import City
from app.modules.cities.schema import CityRead

class CityRepository(BaseRepository[City, CityRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=City, db=db)

    async def get_nearest(self, lat: float, lng: float, params: Params):
        limit = params.size
        offset = (params.page - 1) * limit
        query = text("""
            SELECT id, name, longitude, latitude,
                ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
            FROM cities
            WHERE location IS NOT NULL
            ORDER BY distance
            LIMIT :limit OFFSET :offset
        """)
        result = await self.db.execute(query, {
            "lng": lng,
            "lat": lat,
            "limit": limit,
            "offset": offset
        })
        rows = result.fetchall()

        count_result = await self.db.execute(
            text("SELECT COUNT(*) FROM cities WHERE location IS NOT NULL")
        )
        total = count_result.scalar_one()

        return {"items": rows, "total": total}
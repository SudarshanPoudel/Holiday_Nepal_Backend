from typing import Any, List, Optional
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload , joinedload
from app.core.repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Params

from app.modules.cities.models import City
from app.modules.cities.schema import CityRead
from app.utils.embeddings import get_embedding

class CityRepository(BaseRepository[City, CityRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=City, db=db)


    async def vector_search(self, query: str, limit: int = 10, load_relations: Optional[List[str]] = None, extra_conditions: Optional[List[Any]] = None) -> List[City]:
        embedding = get_embedding(query)
        stmt = select(City).where(City.embedding != None)
        if load_relations:
            for relation in load_relations:
                if '.' in relation:
                    parts = relation.split('.')
                    current_model = City
                    option = None
                    for part in parts:
                        attr = getattr(current_model, part)
                        current_model = attr.property.mapper.class_
                        option = joinedload(attr) if option is None else option.joinedload(attr)
                    stmt = stmt.options(option)
                else:
                    stmt = stmt.options(selectinload(getattr(City, relation)))

        if extra_conditions:
            for condition in extra_conditions:
                stmt = stmt.filter(condition)
                
        stmt = stmt.order_by(City.embedding.cosine_distance(embedding)).limit(limit)
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
    
    async def get_nearest(self, lat: float, lng: float, params: Params, search: str = None):
        limit = params.size
        offset = (params.page - 1) * limit

        base_query = """
            SELECT id, name, longitude, latitude,
                ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
            FROM cities
            WHERE location IS NOT NULL
                AND NOT (longitude = :lng AND latitude = :lat)
                {search_clause}
            ORDER BY distance
            LIMIT :limit OFFSET :offset
        """

        count_query = """
            SELECT COUNT(*)
            FROM cities
            WHERE location IS NOT NULL
                AND NOT (longitude = :lng AND latitude = :lat)
                {search_clause}
        """

        params_dict = {
            "lng": lng,
            "lat": lat,
            "limit": limit,
            "offset": offset,
        }

        if search:
            search_clause = "AND name ILIKE :search"
            params_dict["search"] = f"%{search}%"
        else:
            search_clause = ""

        query = text(base_query.format(search_clause=search_clause))
        result = await self.db.execute(query, params_dict)
        rows = result.fetchall()

        count_sql = text(count_query.format(search_clause=search_clause))
        count_result = await self.db.execute(count_sql, params_dict if search else {"lng": lng, "lat": lat})
        total = count_result.scalar_one()

        return {"items": rows, "total": total}

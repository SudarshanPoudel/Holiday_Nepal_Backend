from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.cities.graph import CityGraphRepository, CityNode
from app.modules.cities.repository import CityRepository
from app.modules.cities.schema import CityRead, CityCreate, CityNearest
from fastapi_pagination import Params
from neo4j import AsyncSession as Neo4jSession
from app.core.schemas import BaseResponse

class CityController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.city_repo = CityRepository(db)
        self.graph_repository = CityGraphRepository(graph_db)

    async def add_city(self, city: CityCreate):
        res = await self.city_repo.create(city)
        await self.graph_repository.create(CityNode(id=res.id, name=res.name))
        return BaseResponse(message="City created successfully", data={"id": res.id, **city.model_dump()})
    
    async def update_city(self, city_id: int, city: CityCreate):
        res = await self.city_repo.update(city_id, city)
        if not res:
            raise HTTPException(status_code=404, detail="City not found")
        await self.graph_repository.update(CityNode(id=res.id, name=res.name))
        return BaseResponse(message="City updated successfully", data={"id": res.id, **city.model_dump()})
    
    async def delete_city(self, city_id: int):
        city = await self.city_repo.delete(city_id)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        await self.graph_repository.delete(city_id)
        return BaseResponse(message="City deleted successfully")
    
    async def index(self, search: str, params: Params):
        res = await self.city_repo.index(
            params=params,
            search_fields=["name"],
            search_query=search,
        )
        if not res:
            raise HTTPException(status_code=404, detail="Cities not found")
        return BaseResponse(message="Cities fetched successfully", data=[CityRead.model_validate(m, from_attributes=True) for m in res.items])
    

    async def nearest(self, latitude: float, longitude: float, params: Params):
        res = await self.city_repo.get_nearest(latitude, longitude, params)
        items = res["items"]
        if not items:
            raise HTTPException(status_code=404, detail="No nearby cities found")

        validated = [
            CityNearest(
                id=row.id,
                name=row.name,
                longitude=row.longitude,
                latitude=row.latitude,
                distance=row.distance
            )
            for row in items
        ]
        return BaseResponse(message="Nearest cities fetched successfully", data=validated)

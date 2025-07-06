from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.cities.repository import CityRepository
from app.modules.cities.schema import CityBase, CityNearest
from fastapi_pagination import Params

from app.core.schemas import BaseResponse

class CityController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.city_repo = CityRepository(db)

    async def index(self, search: str, params: Params):
        res = await self.city_repo.index(
            params=params,
            search_fields=["name"],
            search_query=search,
        )
        if not res:
            raise HTTPException(status_code=404, detail="Cities not found")
        return BaseResponse(message="Cities fetched successfully", data=[CityBase.model_validate(m, from_attributes=True) for m in res.items])
    

    async def nearest(self, lng: float, lat: float, params: Params):
        res = await self.city_repo.get_nearest(lng, lat, params)
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

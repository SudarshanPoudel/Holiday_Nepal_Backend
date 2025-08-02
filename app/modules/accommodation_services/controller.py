from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.accommodation_services.repository import AccomodationServiceRepository
from app.modules.accommodation_services.schema import AccomodationServiceBase, AccomodationServiceCreate, AccomodationServiceRead


class AccomodationServiceController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AccomodationServiceRepository(db)

    async def create(self, accommodation_service: AccomodationServiceCreate):
        res = await self.repository.create(AccomodationServiceBase(**accommodation_service.model_dump(exclude={"image_ids"})))
        await self.repository.add_images(res.id, accommodation_service.image_ids)
        return BaseResponse(message="Accomodation service created successfully", data={'id':res.id, **accommodation_service.model_dump()})
    
    async def update(self, accommodation_service_id: int, accommodation_service: AccomodationServiceCreate):
        res = await self.repository.update(accommodation_service_id, AccomodationServiceBase(**accommodation_service.model_dump(exclude={"image_ids"})))
        await self.repository.update_images(accommodation_service_id, accommodation_service.image_ids)
        return BaseResponse(message="Accomodation service updated successfully", data={'id':res.id, **accommodation_service.model_dump()})
    
    async def get(self, accommodation_service_id: int):
        res = await self.repository.get(accommodation_service_id, load_relations=["images", "city"])
        if not res:
            raise HTTPException(status_code=404, detail="Accomodation service not found")
        return BaseResponse(message="Accomodation service fetched successfully", data=AccomodationServiceRead.model_validate(res, from_attributes=True))
    
    async def delete(self, accommodation_service_id: int):
        delete = await self.repository.delete(accommodation_service_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Accomodation service not found")
        return BaseResponse(message="Accomodation service deleted successfully")

    async def index(
        self,
        params: Params,
        search: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None,
        sort_by: Optional[str] = "id",
        order: Optional[str] = "asc",
    ):
        data = await self.repository.index(
            params=params,
            filters=filters,
            search_fields=["name"],
            search_query=search,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["images", "city"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[AccomodationServiceRead.model_validate(ts, from_attributes=True) for ts in data.items])
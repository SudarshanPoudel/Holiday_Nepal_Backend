from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.accomodation_service.repository import AccomodationServiceRepository
from app.modules.accomodation_service.schema import AccomodationServiceCreate, AccomodationServiceCreateInternal, AccomodationServiceRead, AccomodationServiceUpdate
from app.modules.service_provider.repository import ServiceProviderRepository


class AccomodationServiceController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.repository = AccomodationServiceRepository(db)
        self.service_provider_repository = ServiceProviderRepository(db)

    async def create(self, accomodation_service: AccomodationServiceCreate):
        service_provider_id = await self.service_provider_repository.get_id_by_user_id(self.user_id)
        if not service_provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")

        service = AccomodationServiceCreateInternal(
            service_provider_id=service_provider_id,
            **accomodation_service.model_dump(exclude={"image_ids"})
        )

        res = await self.repository.create(service)
        await self.repository.add_images(res.id, accomodation_service.image_ids)
        return BaseResponse(message="Accomodation service created successfully", data={"id": res.id})
    
    async def update(self, accomodation_service_id: int, accomodation_service: AccomodationServiceUpdate):
        res = await self.repository.update(accomodation_service_id, AccomodationServiceCreateInternal(**accomodation_service.model_dump(exclude={"image_ids"})))
        if not res:
            raise HTTPException(status_code=404, detail="Accomodation service not found")

        await self.repository.update_images(accomodation_service_id, accomodation_service.image_ids)
        return BaseResponse(message="Accomodation service updated successfully", data={"id": res.id})
    
    async def get(self, accomodation_service_id: int):
        res = await self.repository.get(accomodation_service_id, load_relations=["images"])
        if not res:
            raise HTTPException(status_code=404, detail="Accomodation service not found")
        return BaseResponse(message="Accomodation service fetched successfully", data=AccomodationServiceRead.model_validate(res, from_attributes=True))
    
    async def get_all(self):
        res = await self.repository.get_all(load_relations=["images"])
        return BaseResponse(message="Accomodation services fetched successfully", data=[AccomodationServiceRead.model_validate(as_, from_attributes=True) for as_ in res])
    
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
            load_relations=["images"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[AccomodationServiceRead.model_validate(ts, from_attributes=True) for ts in data.items])
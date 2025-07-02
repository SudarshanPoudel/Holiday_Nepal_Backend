from typing import Dict, Optional
from fastapi import HTTPException, Request
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.service_provider.models import ServiceProvider
from app.modules.service_provider.repository import ServiceProviderRepository
from app.modules.service_provider.schema import ServiceProviderRead, ServiceProviderRegister, ServiceProviderRegisterInternal, ServiceProviderUpdate


class ServiceProviderController():
    def __init__(self, db: AsyncSession, request: Request):
        self.db = db
        self.user_id = request.state.user_id
        self.repository = ServiceProviderRepository(db)

    async def register(self, provider: ServiceProviderRegister):
        if await self.repository.get_id_by_user_id(self.user_id):
            raise HTTPException(status_code=400, detail="Service provider already registered")
        provider_internal = ServiceProviderRegisterInternal(user_id=self.user_id, **provider.model_dump())
        res = await self.repository.create(provider_internal)
        return BaseResponse(message="Service provider registered successfully", data={"id": res.id})
        
    async def update(self, provider: ServiceProviderUpdate):
        provider_id = await self.repository.get_id_by_user_id(self.user_id)
        if not provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")
        res = await self.repository.update(provider_id, provider)
        return BaseResponse(message="Service provider updated successfully", data={"id": res.id})
    
    async def get(self, provider_id: int):
        res = await self.repository.get(provider_id)
        if not res:
            raise HTTPException(status_code=404, detail="Service provider not found")
        return BaseResponse(message="Service provider fetched successfully", data=ServiceProviderRead.model_validate(res, from_attributes=True))
    
    async def get_current(self):
        provider_id = await self.repository.get_id_by_user_id(self.user_id)
        if not provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")
        res = await self.repository.get(provider_id)
        return BaseResponse(message="Service provider fetched successfully", data=ServiceProviderRead.model_validate(res, from_attributes=True))
        
    async def delete(self):
        provider_id = await self.repository.get_id_by_user_id(self.user_id)
        if not provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")
        await self.repository.delete(provider_id)
        return BaseResponse(message="Service provider deleted successfully")
    
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
        )
        return BaseResponse(message="Transport services fetched successfully", data=[ServiceProviderRead.model_validate(ts, from_attributes=True) for ts in data.items])

    async def _add_route_segments(self, transport_service_id: int, route_ids: list[int]):
        for route_id in route_ids:
            await self.repository.add_route_segment(transport_service_id, route_id)

    
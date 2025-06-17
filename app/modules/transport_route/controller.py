from typing import Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_route.schema import TransportRouteCreate, TransportRouteRead, TransportRouteUpdate


class TransportRouteController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TransportRouteRepository(db)

    
    async def create(self, transport_route: TransportRouteCreate):
        does_exist = await self.repository.get_all_filtered(filters={"start_municipality_id": transport_route.start_municipality_id, "end_municipality_id": transport_route.end_municipality_id, "route_category": transport_route.route_category})
        if does_exist:
            raise HTTPException(status_code=400, detail="Transport route already exists")
        res = await self.repository.create(transport_route)
        return BaseResponse(message="Transport route created successfully", data={"id": res.id})
    
    async def get_all(self):
        res = await self.repository.get_all(load_relations=["start_municipality", "end_municipality"])
        return BaseResponse(message="Transport routes fetched successfully", data=[TransportRouteRead.model_validate(tr, from_attributes=True) for tr in res])
    
    async def get(self, transport_route_id: int):
        res = await self.repository.get(transport_route_id, load_relations=["start_municipality", "end_municipality"])
        if not res:
            raise HTTPException(status_code=404, detail="Transport route not found")
        return BaseResponse(message="Transport route fetched successfully", data=TransportRouteRead.model_validate(res, from_attributes=True))
    
    async def get_from_municipality(self, municipality_id: int):
        res = await self.repository.get_from_municipality(municipality_id, load_relations=["start_municipality", "end_municipality"])
        if not res:
            raise HTTPException(status_code=404, detail="Transport routes not found")
        return BaseResponse(message="Transport routes fetched successfully", data=[TransportRouteRead.model_validate(tr, from_attributes=True) for tr in res])
    
    async def update(self, transport_route_id: int, transport_route: TransportRouteUpdate):
        res = await self.repository.update(transport_route_id, transport_route)
        if not res:
            raise HTTPException(status_code=404, detail="Transport route not found")
        return BaseResponse(message="Transport route updated successfully", data={"id": res.id})
    
    async def delete(self, transport_route_id: int):
        delete = await self.repository.delete(transport_route_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Transport route not found")
        return BaseResponse(message="Transport route deleted successfully")
    
    async def index(
        self,
        params: Params,
        sort_by: Optional[str],
        order: Optional[str],
    ):
        data = await self.repository.index(
            params=params,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["start_municipality", "end_municipality"]
        )
        return BaseResponse(message="Transport routes fetched successfully", data=[TransportRouteRead.model_validate(tr, from_attributes=True) for tr in data.items])
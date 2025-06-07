from tracemalloc import start
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.service_provider.repository import ServiceProviderRepository
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.repository import TransportServiceRepository
from app.modules.transport_service.schema import TransportServiceBase, TransportServiceCreate, TransportServiceUpdate


class TransportServiceController():
    def __init__(self, db: AsyncSession, request: Request):
        self.db = db
        self.user_id = request.state.user_id
        self.repository = TransportServiceRepository(db)
        self.route_repository = TransportRouteRepository(db)
        self.service_provider_repository = ServiceProviderRepository(db)

    async def create(self, transport_service: TransportServiceCreate):
        service_provider_id = await self.service_provider_repository.get_id_by_user_id(self.user_id)
        if not service_provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")
        start = await self.route_repository.get(transport_service.route_ids[0])
        end = await self.route_repository.get(transport_service.route_ids[-1])

        if not start or not end:
            raise HTTPException(status_code=404, detail="Route not found")
        
        total_distance = 0
        for route in transport_service.route_ids:
            route = await self.route_repository.get(route)
            total_distance += route.distance
        
        service = TransportServiceBase(
            service_provider_id=service_provider_id,
            start_municipality_id=start.id,
            end_municipality_id=end.id,
            description=transport_service.description,
            route_category=transport_service.route_category,
            transport_category=transport_service.transport_category,
            average_time=transport_service.average_time,
            total_distance=total_distance
        )

        res = await self.repository.create(service)
        try:
            await self.repository.add_route_segment(res.id, transport_service.route_ids)
        except Exception as e:
            self.repository.delete(res.id)
            raise e
        return BaseResponse(message="Transport service created successfully", data={"id": res.id})
    

    async def get(self, transport_service_id: int):
        res = await self.repository.get(transport_service_id)
        if not res:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(message="Transport service fetched successfully", data=TransportServiceBase.model_validate(res, from_attributes=True))
    
    async def get_all(self):
        res = await self.repository.get_all()
        return BaseResponse(message="Transport services fetched successfully", data=[TransportServiceBase.model_validate(ts, from_attributes=True) for ts in res])
    
    async def update(self, transport_service_id: int, transport_service: TransportServiceUpdate):
        start = await self.route_repository.get(transport_service.route_ids[0]) #TODO: Fix this
        end = await self.route_repository.get(transport_service.route_ids[-1])

        if not start or not end:
            raise HTTPException(status_code=404, detail="Route not found")
        
        total_distance = 0
        for route in transport_service.route_ids:
            route = await self.route_repository.get(route)
            total_distance += route.distance
        
        service = TransportServiceBase(
            service_provider_id=transport_service.service_provider_id,
            start_municipality_id=start.id,
            end_municipality_id=end.id,
            description=transport_service.description,
            route_category=transport_service.route_category,
            transport_category=transport_service.transport_category,
            average_time=transport_service.average_time,
            total_distance=total_distance
        )

        res = await self.repository.update(transport_service_id, service)
        if not res:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(message="Transport service updated successfully", data={"id": res.id})
    

    async def delete(self, transport_service_id: int):
        delete = await self.repository.delete(transport_service_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(message="Transport service deleted successfully")
    

    async def _add_route_segments(self, transport_service_id: int, route_ids: list[int]):
        for route_id in route_ids:
            await self.repository.add_route_segment(transport_service_id, route_id)
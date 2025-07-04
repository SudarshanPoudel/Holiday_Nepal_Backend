from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.service_provider.repository import ServiceProviderRepository
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.repository import TransportServiceRepository
from app.modules.transport_service.schema import TransportServiceBase, TransportServiceCreate, TransportServiceRead, TransportServiceReadAll, TransportServiceUpdate


class TransportServiceController:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.repository = TransportServiceRepository(db)
        self.route_repository = TransportRouteRepository(db)
        self.service_provider_repository = ServiceProviderRepository(db)

    async def create(self, transport_service: TransportServiceCreate):
        service_provider_id = await self.service_provider_repository.get_id_by_user_id(self.user_id)
        if not service_provider_id:
            raise HTTPException(status_code=404, detail="Service provider not found")

        start_route = await self.route_repository.get(transport_service.route_ids[0])
        end_route = await self.route_repository.get(transport_service.route_ids[-1])
        if not start_route or not end_route:
            raise HTTPException(status_code=404, detail="Invalid route(s)")

        total_distance = 0
        for route_id in transport_service.route_ids:
            route = await self.route_repository.get(route_id)
            if not route:
                raise HTTPException(status_code=404, detail=f"Route with id {route_id} not found")
            total_distance += route.distance

        service = TransportServiceBase(
            service_provider_id=service_provider_id,
            start_municipality_id=start_route.start_municipality_id,
            end_municipality_id=end_route.end_municipality_id,
            description=transport_service.description,
            route_category=transport_service.route_category,
            transport_category=transport_service.transport_category,
            average_time=transport_service.average_time,
            total_distance=total_distance,
            image_ids=transport_service.image_ids,
        )

        res = await self.repository.create(service)

        try:
            await self.repository.add_route_segment(res.id, transport_service.route_ids)
            if transport_service.image_ids:
                await self.repository.attach_images(res.id, transport_service.image_ids)
        except Exception as e:
            await self.repository.delete(res.id)
            raise e

        return BaseResponse(message="Transport service created successfully", data={"id": res.id})

    async def get(self, transport_service_id: int):
        res = await self.repository.get(
            transport_service_id,
            load_relations=[
                "images",
                "start_municipality",
                "end_municipality",
                "route_segments.route.start_municipality",
                "route_segments.route.end_municipality"
            ],
        )
        if not res:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(
            message="Transport service fetched successfully",
            data=TransportServiceRead.model_validate(res, from_attributes=True),
        )

    async def update(self, transport_service_id: int, transport_service: TransportServiceUpdate):
        existing = await self.repository.get(transport_service_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Transport service not found")

        start = existing.start_municipality_id
        end = existing.end_municipality_id
        total_distance = existing.total_distance

        # Optional update to route IDs and recalculate distance if provided
        if hasattr(transport_service, 'route_ids') and transport_service.route_ids:
            start_route = await self.route_repository.get(transport_service.route_ids[0])
            end_route = await self.route_repository.get(transport_service.route_ids[-1])
            if not start_route or not end_route:
                raise HTTPException(status_code=404, detail="Invalid route(s)")

            start = start_route.start_municipality_id
            end = end_route.end_municipality_id

            total_distance = 0
            for route_id in transport_service.route_ids:
                route = await self.route_repository.get(route_id)
                if not route:
                    raise HTTPException(status_code=404, detail=f"Route with id {route_id} not found")
                total_distance += route.distance

            await self.repository.clear_route_segments(transport_service_id)
            await self.repository.add_route_segment(transport_service_id, transport_service.route_ids)

        service = TransportServiceBase(
            service_provider_id=transport_service.service_provider_id or existing.service_provider_id,
            start_municipality_id=start,
            end_municipality_id=end,
            description=transport_service.description or existing.description,
            route_category=transport_service.route_category or existing.route_category,
            transport_category=transport_service.transport_category or existing.transport_category,
            average_time=transport_service.average_time or existing.average_time,
            total_distance=total_distance,
            image_ids=transport_service.image_ids or [img.id for img in existing.images],
        )

        res = await self.repository.update(transport_service_id, service)
        await self.repository.replace_images(transport_service_id, service.image_ids)

        return BaseResponse(message="Transport service updated successfully", data={"id": res.id})

    async def delete(self, transport_service_id: int):
        deleted = await self.repository.delete(transport_service_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(message="Transport service deleted successfully")
    
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
            load_relations=["images", "start_municipality", "end_municipality"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[TransportServiceReadAll.model_validate(ts, from_attributes=True) for ts in data.items])

    async def _add_route_segments(self, transport_service_id: int, route_ids: list[int]):
        for route_id in route_ids:
            await self.repository.add_route_segment(transport_service_id, route_id)

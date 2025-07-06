from fastapi import HTTPException
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.repository import BaseRepository
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.models import TransportService, TransportServiceRouteSegment, transport_service_images
from app.modules.transport_service.schema import TransportServiceBase

class TransportServiceRepository(BaseRepository[TransportService, TransportServiceBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(TransportService, db)


    async def add_route_segment(self, transport_service_id: int, route_ids: list[int]):
        last_place = None
        route_repo = TransportRouteRepository(self.db)

        try:
            for i, route_id in enumerate(route_ids):
                route = await route_repo.get(route_id)
                if not route:
                    raise HTTPException(status_code=404, detail=f"Route with ID {route_id} not found")
                if not last_place:
                    last_place = route.end_municipality_id
                elif last_place == route.start_municipality_id:
                    last_place = route.end_municipality_id
                elif last_place == route.end_municipality_id:
                    last_place = route.start_municipality_id
                else:
                    raise HTTPException(status_code=400, detail="Invalid route index")

                last_place = route.end_municipality_id

                segment = TransportServiceRouteSegment(
                    service_id=transport_service_id,
                    route_id=route_id,
                    index=i
                )
                self.db.add(segment)

            await self.db.commit()
        except SQLAlchemyError as e:
            import traceback
            traceback.print_exc()
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to add route segments")
            
    async def attach_images(self, service_id: int, image_ids: list[int]):
        await self.db.execute(insert(transport_service_images).values([
            {"transport_service_id": service_id, "image_id": img_id} for img_id in image_ids
        ]))
        await self.db.commit()

    async def replace_images(self, service_id: int, image_ids: list[int]):
        await self.db.execute(delete(transport_service_images).where(transport_service_images.c.transport_service_id == service_id))
        await self.attach_images(service_id, image_ids)

    async def clear_route_segments(self, service_id: int):
        await self.db.execute(delete(TransportServiceRouteSegment).where(TransportServiceRouteSegment.transport_service_id == service_id))
        await self.db.commit()

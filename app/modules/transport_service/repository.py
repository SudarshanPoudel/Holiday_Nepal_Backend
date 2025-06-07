from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.repository import BaseRepository
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.models import TransportService, TransportServiceRouteSegment
from app.modules.transport_service.schema import TransportServiceBase

class TransportServiceRepository(BaseRepository[TransportService, TransportServiceBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(TransportService, db)


    async def add_route_segment(self, transport_service_id: int, route_ids: list[int]):
        last_route_place = None
        route_repo = TransportRouteRepository(self.db)

        try:
            for i, route_id in enumerate(route_ids):
                route = await route_repo.get(route_id)
                if not route:
                    raise HTTPException(status_code=404, detail=f"Route with ID {route_id} not found")

                if last_route_place and route.start_municipality_id != last_route_place:
                    raise HTTPException(status_code=400, detail="Route segments must be connected")

                last_route_place = route.end_municipality_id

                segment = TransportServiceRouteSegment(
                    service_id=transport_service_id,
                    route_id=route_id,
                    sequence=i
                )
                self.db.add(segment)

            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to add route segments")
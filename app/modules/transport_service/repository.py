from typing import List

from fastapi import HTTPException
from sqlalchemy import  select, delete, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.repository import BaseRepository
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.transport_route.models import TransportRoute
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.models import (
    TransportService,
    TransportServiceRouteSegment,
    transport_service_images
)
from app.modules.transport_service.schema import TransportServiceBase


class TransportServiceRepository(BaseRepository[TransportService, TransportServiceBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(TransportService, db)

    async def add_route_segment(self, service_id: int, route_ids: list[int]):
        route_repo = TransportRouteRepository(self.db)

        last_place = None
        start_city_id = None
        try:
            segments = []
            for i, route_id in enumerate(route_ids):
                route = await route_repo.get(route_id)
                if not route:
                    raise HTTPException(status_code=404, detail=f"Route with ID {route_id} not found")

                if last_place is None:
                    if i + 1 < len(route_ids):
                        next_route = await route_repo.get(route_ids[i + 1])
                        if route.start_city_id in (next_route.start_city_id, next_route.end_city_id):
                            last_place = route.start_city_id
                            start_city_id = route.end_city_id
                        else:
                            last_place = route.end_city_id
                            start_city_id = route.start_city_id
                    else:
                        # only one route
                        last_place = route.end_city_id
                        start_city_id = route.start_city_id

                elif last_place == route.start_city_id:
                    last_place = route.end_city_id
                elif last_place == route.end_city_id:
                    last_place = route.start_city_id
                else:
                    print(last_place, route.start_city_id, route.end_city_id)
                    raise HTTPException(status_code=400, detail="Invalid route index")

                segment = TransportServiceRouteSegment(
                    service_id=service_id,
                    route_id=route_id,
                    index=i
                )
                self.db.add(segment)
                await self.db.flush()
                segments.append(segment)

            await self.db.commit()

            return {
                "segments": segments,
                "start_city_id": start_city_id,
                "end_city_id": last_place,
            }

        except SQLAlchemyError:
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
        await self.db.execute(delete(TransportServiceRouteSegment).where(TransportServiceRouteSegment.service_id == service_id))
        await self.db.commit()
                
    async def recommend_services(self, start_city_id: int, end_city_id: int) -> List[int]:
        # Step 2: Get all route IDs that start or end at those cities
        route_query = select(TransportRoute.id, TransportRoute.start_city_id, TransportRoute.end_city_id)
        routes_result = await self.db.execute(route_query)
        routes = routes_result.all()

        # Split route IDs into two sets
        start_city_route_ids = {r.id for r in routes if r.start_city_id == start_city_id or r.end_city_id == start_city_id}
        end_city_route_ids = {r.id for r in routes if r.start_city_id == end_city_id or r.end_city_id == end_city_id}

        if not start_city_route_ids or not end_city_route_ids:
            return []

        # Step 3: Find all transport service route segments
        ts_segment_query = select(
            TransportServiceRouteSegment.service_id,
            TransportServiceRouteSegment.route_id
        )
        segment_result = await self.db.execute(ts_segment_query)
        segments = segment_result.all()

        # Step 4: Group routes per service
        service_to_routes = {}
        for row in segments:
            service_to_routes.setdefault(row.service_id, set()).add(row.route_id)

        # Step 5: Score and rank in Python
        recommendations = []
        for service_id, route_ids in service_to_routes.items():
            start_match = bool(route_ids & start_city_route_ids)
            end_match = bool(route_ids & end_city_route_ids)

            if not (start_match and end_match):
                continue  # skip services that don’t touch both ends

            # Priority scoring
            if route_ids & start_city_route_ids and route_ids & end_city_route_ids:
                priority = 1
                # Optional: boost if both directly match route start/end
                if start_city_route_ids & route_ids and end_city_route_ids & route_ids:
                    priority = 2
            else:
                priority = 0

            recommendations.append({
                "id": service_id,
                "priority": priority,
            })

        # Optional: fetch cost/distance for sorting
        if not recommendations:
            return []

        service_ids = [r["id"] for r in recommendations]
        svc_query = select(
            TransportService.id,
            TransportService.cost,
            TransportService.total_distance,
            TransportService.average_duration
        ).where(TransportService.id.in_(service_ids))
        svc_result = await self.db.execute(svc_query)
        svc_data = {row.id: row for row in svc_result}

        # Merge and sort
        for r in recommendations:
            svc = svc_data.get(r["id"])
            cost = svc.cost or 0
            distance = svc.total_distance or 1
            r["cost_per_distance"] = cost / distance
            r["duration"] = svc.average_duration or 0

        sorted_ids = [
            r["id"]
            for r in sorted(
                recommendations,
                key=lambda r: (-r["priority"], r["cost_per_distance"], r["duration"])
            )
        ]

        return sorted_ids
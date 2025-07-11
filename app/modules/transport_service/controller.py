from re import S
from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.transport_service.graph import TransportServiceCityEdge, TransportServiceGraphRepository, TransportServiceNode, TransportServiceRouteHopCityEdge, TransportServiceRouteHopGraphRepository, TransportServiceRouteHopNode, TransportServiceRouteHopTransportServiceRouteHopEdge, TransportServiceTransportRouteHopEdge
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_service.repository import TransportServiceRepository
from app.modules.transport_service.schema import TransportServiceBase, TransportServiceCreate, TransportServiceRead, TransportServiceReadAll


class TransportServiceController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = TransportServiceRepository(db)
        self.route_repository = TransportRouteRepository(db)
        self.graph_repository = TransportServiceGraphRepository(graph_db)
        self.route_hop_graph_repository = TransportServiceRouteHopGraphRepository(graph_db)

    async def create(self, transport_service: TransportServiceCreate):
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
            start_city_id=start_route.start_city_id,
            end_city_id=end_route.end_city_id,
            description=transport_service.description,
            route_category=transport_service.route_category,
            transport_category=transport_service.transport_category,
            average_duration=transport_service.average_duration,
            total_distance=total_distance,
            cost=transport_service.cost
        )

        res = await self.repository.create(service)
        await self.graph_repository.create(
            TransportServiceNode(
                id=res.id,
                start_city_id=start_route.start_city_id,
                end_city_id=end_route.end_city_id,
                route_category=transport_service.route_category,
                transport_category=transport_service.transport_category,
                total_distance=total_distance,
                average_duration=transport_service.average_duration,
                cost=transport_service.cost
            ))
        await self.graph_repository.add_edge(
            TransportServiceCityEdge(
                source_id=res.id,
                target_id=start_route.start_city_id
            ))

        try:
            segments = await self.repository.add_route_segment(res.id, transport_service.route_ids)
            last_segment = None
            
            for (i, segment) in enumerate(segments):
                route = await self.route_repository.get(segment.route_id)
                await self.route_hop_graph_repository.create(
                    TransportServiceRouteHopNode(id=segment.id, route_id=segment.route_id)
                )
                await self.route_hop_graph_repository.add_edge(
                    TransportServiceRouteHopCityEdge(source_id=segment.id, target_id=route.end_city_id)
                )
                if last_segment is None:
                    await self.graph_repository.add_edge(
                        TransportServiceTransportRouteHopEdge(
                            source_id=res.id,
                            target_id=segment.id,
                        )
                    )
                else:
                    await self.route_hop_graph_repository.add_edge(
                        TransportServiceRouteHopTransportServiceRouteHopEdge(
                            source_id=last_segment.id,
                            target_id=segment.id,
                        )
                    )
                last_segment = segment


            if transport_service.image_ids:
                await self.repository.attach_images(res.id, transport_service.image_ids)
        except Exception as e:
            await self.repository.delete(res.id)
            raise e
        service = await self.repository.get(res.id, load_relations=["images", "start_city", "end_city", "route_segments.route.start_city", "route_segments.route.end_city"])
        return BaseResponse(message="Transport service created successfully", data=TransportServiceRead.model_validate(service, from_attributes=True))

    async def get(self, transport_service_id: int):
        res = await self.repository.get(
            transport_service_id,
            load_relations=[
                "images",
                "start_city",
                "end_city",
                "route_segments.route.start_city",
                "route_segments.route.end_city"
            ],
        )
        if not res:
            raise HTTPException(status_code=404, detail="Transport service not found")
        return BaseResponse(
            message="Transport service fetched successfully",
            data=TransportServiceRead.model_validate(res, from_attributes=True),
        )

    async def update(self, transport_service_id: int, transport_service: TransportServiceCreate):
        existing = await self.repository.get(transport_service_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Transport service not found")

        start = existing.start_city_id
        end = existing.end_city_id
        total_distance = existing.total_distance

        # Optional update to route IDs and recalculate distance if provided
        if hasattr(transport_service, 'route_ids') and transport_service.route_ids:
            start_route = await self.route_repository.get(transport_service.route_ids[0])
            end_route = await self.route_repository.get(transport_service.route_ids[-1])
            if not start_route or not end_route:
                raise HTTPException(status_code=404, detail="Invalid route(s)")

            start = start_route.start_city_id
            end = end_route.end_city_id

            total_distance = 0
            for route_id in transport_service.route_ids:
                route = await self.route_repository.get(route_id)
                if not route:
                    raise HTTPException(status_code=404, detail=f"Route with id {route_id} not found")
                total_distance += route.distance

            await self.repository.clear_route_segments(transport_service_id)
            segments = await self.repository.add_route_segment(transport_service_id, transport_service.route_ids)

        service = TransportServiceBase(
            start_city_id=start,
            end_city_id=end,
            description=transport_service.description or existing.description,
            route_category=transport_service.route_category or existing.route_category,
            transport_category=transport_service.transport_category or existing.transport_category,
            average_duration=transport_service.average_duration or existing.average_duration,
            total_distance=total_distance,
            cost=transport_service.cost 
        )

        res = await self.repository.update(transport_service_id, service)
        
        try:
            await self.graph_repository.delete(transport_service_id)
        except Exception as e:
            print(f"Error deleting from graph database: {e}")
        
        await self.graph_repository.create(
            TransportServiceNode(
                id=transport_service_id,
                start_city_id=start,
                end_city_id=end,
                route_category=transport_service.route_category or existing.route_category,
                transport_category=transport_service.transport_category or existing.transport_category,
                total_distance=total_distance,
                average_duration=transport_service.average_duration or existing.average_duration,
                cost=transport_service.cost or existing.cost
            )
        )
        await self.graph_repository.add_edge(
            TransportServiceCityEdge(
                source_id=res.id,
                target_id=start_route.start_city_id
            ))
        
        # Recreate all route hop relationships
        last_segment = None
        
        for (i, segment) in enumerate(segments):
            route = await self.route_repository.get(segment.route_id)
            await self.route_hop_graph_repository.create(
                TransportServiceRouteHopNode(id=segment.id, route_id=segment.route_id)
            )
            await self.route_hop_graph_repository.add_edge(
                TransportServiceRouteHopCityEdge(source_id=segment.id, target_id=route.end_city_id)
            )
            if last_segment is None:
                await self.graph_repository.add_edge(
                    TransportServiceTransportRouteHopEdge(
                        source_id=transport_service_id,
                        target_id=segment.id,
                    )
                )
            else:
                await self.route_hop_graph_repository.add_edge(
                    TransportServiceRouteHopTransportServiceRouteHopEdge(
                        source_id=last_segment.id,
                        target_id=segment.id,
                    )
                )
            last_segment = segment
        
        await self.repository.replace_images(transport_service_id, transport_service.image_ids)
        service = await self.repository.get(res.id, load_relations=["images", "start_city", "end_city", "route_segments.route.start_city", "route_segments.route.end_city"])
        return BaseResponse(message="Transport service updated successfully", data=TransportServiceRead.model_validate(service, from_attributes=True))

    async def delete(self, transport_service_id: int):
        deleted = await self.repository.delete(transport_service_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Transport service not found")
        await self.graph_repository.delete(transport_service_id)
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
            load_relations=["images", "start_city", "end_city"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[TransportServiceReadAll.model_validate(ts, from_attributes=True) for ts in data.items])

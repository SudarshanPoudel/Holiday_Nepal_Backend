from typing import Optional
from fastapi import HTTPException
from app.modules.cities.graph import CityGraphRepository
from app.modules.transport_route.graph import TransportRouteEdge
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_route.schema import RouteCategoryEnum, TransportRouteCreate, TransportRouteRead, TransportRouteUpdate


class TransportRouteController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = TransportRouteRepository(db)
        self.graph_repository = CityGraphRepository(graph_db)

    
    async def create(self, transport_route: TransportRouteCreate):
        does_exist = await self.repository.get_all_filtered(filters={"start_city_id": transport_route.start_city_id, "end_city_id": transport_route.end_city_id, "route_category": transport_route.route_category})
        if does_exist:
            raise HTTPException(status_code=400, detail="Transport route already exists")
        res = await self.repository.create(transport_route)
        await self.graph_repository.add_edge(TransportRouteEdge(
            id=res.id,
            source_id=transport_route.start_city_id,
            target_id=transport_route.end_city_id,
            average_duration=transport_route.average_duration,
            average_cost=transport_route.average_cost,
            distance=transport_route.distance,
            route_category=transport_route.route_category
        ))
        return BaseResponse(message="Transport route created successfully", data={"id": res.id})
    
    async def get(self, transport_route_id: int):
        res = await self.repository.get(transport_route_id, load_relations=["start_city", "end_city"])
        if not res:
            raise HTTPException(status_code=404, detail="Transport route not found")
        return BaseResponse(message="Transport route fetched successfully", data=TransportRouteRead.model_validate(res, from_attributes=True))
    
    async def get_from_city(self, city_id: int, category: Optional[RouteCategoryEnum] = None):
        res = await self.graph_repository.get_edges(TransportRouteEdge, city_id)
        if not res:
            raise HTTPException(status_code=404, detail="Transport routes not found")
        route_ids = [r.id for r in res if not category or r.route_category == category]
        res = await self.repository.get_multiple(route_ids, load_relations=["start_city", "end_city"])
        return BaseResponse(message="Transport routes fetched successfully", data=[TransportRouteRead.model_validate(tr, from_attributes=True) for tr in res])
    
    async def update(self, transport_route_id: int, transport_route: TransportRouteCreate):
        res = await self.repository.update(transport_route_id, transport_route)
        if not res:
            raise HTTPException(status_code=404, detail="Transport route not found")
        await self.graph_repository.update_edge(
            update_data=TransportRouteEdge(
                id=transport_route_id,
                source_id=transport_route.start_city_id,
                target_id=transport_route.end_city_id,
                average_duration=transport_route.average_duration,
                distance=transport_route.distance,
                route_category=transport_route.route_category
            )
        )
        return BaseResponse(message="Transport route updated successfully", data={"id": res.id})
    
    async def delete(self, transport_route_id: int):
        delete = await self.repository.delete(transport_route_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Transport route not found")
        await self.graph_repository.delete_edge(TransportRouteEdge, transport_route_id)
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
            load_relations=["start_city", "end_city"]
        )
        return BaseResponse(message="Transport routes fetched successfully", data=[TransportRouteRead.model_validate(tr, from_attributes=True) for tr in data.items])
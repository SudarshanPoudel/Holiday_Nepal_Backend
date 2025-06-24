from typing import Optional
from fastapi import HTTPException
from app.core.schemas import Neo4jSession, AsyncSession
from app.modules.places.repository import PlaceRepository
from app.modules.transport_route.graph import TransportRouteGraphRepository
from app.modules.transport_route.schema import RouteCategoryEnum


class RouteService():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
    

    def get_possible_next_places(self, municipality_id: int, route_category: Optional[RouteCategoryEnum] = None):
        pass
    
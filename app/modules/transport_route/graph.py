from typing import ClassVar, Optional, Type
from neo4j import AsyncSession
from pydantic import BaseModel
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode, BaseEdge
from app.modules.cities.graph import CityNode
from app.modules.transport_route.schema import RouteCategoryEnum
from neo4j.exceptions import ClientError

class TransportRouteEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_ROUTE"
    source_model: ClassVar[Type[BaseNode]] = CityNode
    target_model: ClassVar[Type[BaseNode]] = CityNode
    distance: float
    average_duration: Optional[float]
    average_cost: Optional[float]
    route_category: RouteCategoryEnum
from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode, BaseEdge
from app.modules.address.graph import MunicipalityNode
from app.modules.transport_route.schema import RouteCategoryEnum


class TransportRouteEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_ROUTE"
    start_id: int
    end_id: int
    average_time: int
    distance: float
    route_category: RouteCategoryEnum
    start_model: ClassVar[Type[BaseNode]] = MunicipalityNode
    end_model: ClassVar[Type[BaseNode]] = MunicipalityNode


class TransportRouteGraphRepository(BaseGraphRepository[TransportRouteEdge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TransportRouteEdge)
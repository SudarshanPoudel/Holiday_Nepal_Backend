from typing import ClassVar, Optional, Type
from neo4j import AsyncSession
from pydantic import BaseModel
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode, BaseEdge
from app.modules.address.graph import MunicipalityNode
from app.modules.transport_route.schema import RouteCategoryEnum


class TransportRouteEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_ROUTE"
    start_model: ClassVar[Type[BaseNode]] = MunicipalityNode
    end_model: ClassVar[Type[BaseNode]] = MunicipalityNode
    average_time: int
    distance: float
    route_category: RouteCategoryEnum

class TransportRouteEdgeRead(BaseModel):
    id: int
    average_time: int
    distance: float
    route_category: RouteCategoryEnum

class TransportRouteGraphRepository(BaseGraphRepository[TransportRouteEdge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TransportRouteEdge)

    async def get_possible_routes_from_municipality(self, municipality_id: int, category: Optional[RouteCategoryEnum] = None) -> list[TransportRouteEdge]:
        base_query = f"""
        MATCH (m1:{self.start_label} {{id: $municipality_id}})-[r:{self.label}]-(m2:{self.end_label})
        """
        if category is not None:
            base_query += "WHERE r.route_category = $category\n"
        base_query += "RETURN r"

        params = {"municipality_id": municipality_id}
        if category is not None:
            params["category"] = category

        result = await self.session.run(base_query, **params)
        records = [record async for record in result]
        return [TransportRouteEdgeRead(**record['r']) for record in records]
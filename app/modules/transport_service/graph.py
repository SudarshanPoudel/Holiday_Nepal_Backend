from typing import ClassVar, List, Optional, Type
from app.core.graph_repository import BaseGraphRepository
from neo4j import AsyncSession
from pydantic import BaseModel
from app.core.graph_schemas import BaseNode, BaseEdge
from app.modules.cities.graph import CityNode
from app.modules.transport_route.schema import RouteCategoryEnum


class TransportServiceNode(BaseNode):
    label: ClassVar[str] = "TransportService"
    child_relationships = {"TRANSPORT_SERVICE_STARTS_AT_ROUTE_HOP": "TransportServiceRouteHop"}
    id: int
    start_city_id: int
    end_city_id: int
    route_category: RouteCategoryEnum
    transport_category: str  
    total_distance: float
    average_duration: Optional[float] = None
    cost: Optional[float] = None

class TransportServiceRouteHopNode(BaseNode):
    label: ClassVar[str] = "TransportServiceRouteHop"
    sequential_child_relationships = {"NEXT_ROUTE_HOP": "TransportServiceRouteHop"}
    id: int
    route_id: int

class TransportServiceTransportRouteHopEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_SERVICE_STARTS_AT_ROUTE_HOP"
    source_model: ClassVar[Type[BaseNode]] = TransportServiceNode
    target_model: ClassVar[Type[BaseNode]] = TransportServiceRouteHopNode

class TransportServiceCityEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_SERVICE_STARTS_AT_CITY"
    source_model: ClassVar[Type[BaseNode]] = TransportServiceNode
    target_model: ClassVar[Type[BaseNode]] = CityNode

class TransportServiceRouteHopCityEdge(BaseEdge):
    label: ClassVar[str] = "TRANSPORT_SERVICE_ROUTE_HOP_VISIT_CITY"
    source_model: ClassVar[Type[BaseNode]] = TransportServiceRouteHopNode
    target_model: ClassVar[Type[BaseNode]] = CityNode


class TransportServiceRouteHopTransportServiceRouteHopEdge(BaseEdge):
    label: ClassVar[str] = "NEXT_ROUTE_HOP"
    source_model: ClassVar[Type[BaseNode]] = TransportServiceRouteHopNode
    target_model: ClassVar[Type[BaseNode]] = TransportServiceRouteHopNode


class TransportServiceGraphRepository(BaseGraphRepository[TransportServiceNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TransportServiceNode)
        
    async def recommend_services_matching_plan_hops(self, plan_day_step_id: str) -> List[int]:
        async def match_services(tx):
            query = """
            MATCH (step:PlanDayStep {id: $plan_day_step_id})-[:PLAN_DAY_STEP_STARTS_AT_PLAN_ROUTE_HOP]->(startHop:PlanRouteHop)
            CALL apoc.path.subgraphNodes(startHop, {
                relationshipFilter: "NEXT_PLAN_ROUTE_HOP>",
                minLevel: 0
            }) YIELD node AS planHop
            MATCH (planHop)-[:PLAN_ROUTE_HOP_VISIT_CITY]->(city:City)
            WITH step, collect(city.id) AS planCityIds
            WITH planCityIds, 
                planCityIds[0] AS planStartCityId,
                planCityIds[-1] AS planEndCityId

            MATCH (ts:TransportService)-[:TRANSPORT_SERVICE_STARTS_AT_ROUTE_HOP]->(startTsHop:TransportServiceRouteHop)
            CALL apoc.path.subgraphNodes(startTsHop, {
                relationshipFilter: "NEXT_ROUTE_HOP>",
                minLevel: 0
            }) YIELD node AS tsHop
            MATCH (tsHop)-[:TRANSPORT_SERVICE_ROUTE_HOP_VISIT_CITY]->(tsCity:City)
            WITH ts, ts.id AS transportServiceId, collect(tsCity.id) AS tsCityIds, planCityIds, planStartCityId, planEndCityId
            WHERE apoc.coll.containsAll(tsCityIds, planCityIds)
            AND ALL(i IN range(0, size(planCityIds) - 2) WHERE
                apoc.coll.indexOf(tsCityIds, planCityIds[i + 1]) > apoc.coll.indexOf(tsCityIds, planCityIds[i])
            )

            WITH transportServiceId, ts, tsCityIds, planCityIds, planStartCityId, planEndCityId,
            CASE
                WHEN tsCityIds = planCityIds THEN 3
                WHEN tsCityIds[0] = planStartCityId THEN 2
                WHEN tsCityIds[-1] = planEndCityId THEN 1
                ELSE 0
            END AS priority,
            CASE WHEN ts.total_distance > 0 THEN ts.cost / ts.total_distance ELSE ts.cost END AS cost_per_distance

            RETURN transportServiceId, priority, cost_per_distance, ts.average_duration
            ORDER BY priority DESC, cost_per_distance ASC, ts.average_duration ASC
            """
            result = await tx.run(query, {"plan_day_step_id": plan_day_step_id})
            return [record["transportServiceId"] async for record in result]

        return await self.session.execute_read(match_services)


class TransportServiceRouteHopGraphRepository(BaseGraphRepository[TransportServiceRouteHopNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TransportServiceRouteHopNode)
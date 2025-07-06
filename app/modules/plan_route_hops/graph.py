from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode, BaseEdge
from app.modules.address.graph import CityNode
from app.modules.plan_day_steps.graph import PlanDayStepNode
from app.modules.transport_route.schema import RouteCategoryEnum


class PlanRouteHopNode(BaseNode):
    label: ClassVar[str] = "PlanRouteHop"
    sequential_child_relationships = {"NEXT_PLAN_ROUTE_HOP": "PlanRouteHop"}
    index: int
    route_id: int
    route_category: RouteCategoryEnum
    segment_duration: float
    segment_cost: float

class PlanDayStepPlanRouteHopEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_DAY_STEP_STARTS_AT_PLAN_ROUTE_HOP"
    source_model: ClassVar[Type[BaseNode]] = PlanDayStepNode
    target_model: ClassVar[Type[BaseNode]] = PlanRouteHopNode

class PlanRouteHopCityEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_ROUTE_HOP_VISIT_CITY"
    source_model: ClassVar[Type[BaseNode]] = PlanRouteHopNode
    target_model: ClassVar[Type[BaseNode]] = CityNode

class PlanRouteHopPlanRouteHopEdge(BaseEdge):
    label: ClassVar[str] = "NEXT_PLAN_ROUTE_HOP"
    source_model: ClassVar[Type[BaseNode]] = PlanRouteHopNode
    target_model: ClassVar[Type[BaseNode]] = PlanRouteHopNode
    

class PlanRouteHopGraphRepository(BaseGraphRepository[PlanRouteHopNode]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PlanRouteHopNode)

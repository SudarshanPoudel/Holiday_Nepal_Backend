from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.activities.graph import ActivityNode
from app.modules.cities.graph import CityNode
from app.modules.places.graph import PlaceNode
from app.modules.plan_day.graph import PlanDayNode
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum
from app.modules.plans.graph import PlanNode

class PlanDayStepNode(BaseNode):
    label: ClassVar[str] = "PlanDayStep"
    child_relationships = {"PLAN_DAY_STEP_STARTS_AT_PLAN_ROUTE_HOP": "PlanRouteHop"}
    sequential_child_relationships = {"NEXT_PLAN_DAY_STEP": "PlanDayStep"}
    index: int
    category: PlanDayStepCategoryEnum
    duration: float
    cost: float
    
class PlanDayPlanDayStepEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_DAY_STARTS_AT_PLAN_DAY_STEP"
    source_model: ClassVar[Type[BaseNode]] = PlanDayNode
    target_model: ClassVar[Type[BaseNode]] = PlanDayStepNode

class PlanDayStepActivityEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_DAY_STEP_DOES_ACTIVITY"
    source_model: ClassVar[Type[BaseNode]] = PlanDayStepNode
    target_model: ClassVar[Type[BaseNode]] = ActivityNode
    cost: float
    duration: float

class PlanDayStepPlaceEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_DAY_STEP_VISIT_PLACE"
    source_model: ClassVar[Type[BaseNode]] = PlanDayStepNode
    target_model: ClassVar[Type[BaseNode]] = PlaceNode
    cost: float
    duration: float

class PlanDayStepPlanDayStepEdge(BaseEdge):
    label: ClassVar[str] = "NEXT_PLAN_DAY_STEP"
    source_model: ClassVar[Type[BaseNode]] = PlanDayStepNode
    target_model: ClassVar[Type[BaseNode]] = PlanDayStepNode

class PlanDayStepGraphRepository(BaseGraphRepository[PlanDayStepNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PlanDayStepNode)


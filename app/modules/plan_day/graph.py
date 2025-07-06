from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.address.graph import CityNode
from app.modules.plans.graph import PlanNode

class PlanDayNode(BaseNode):
    label: ClassVar[str] = "PlanDay"
    child_relationships = {"PLAN_DAY_STARTS_AT_PLAN_DAY_STEP": "PlanDayStep"}
    sequential_child_relationships = {"NEXT_PLAN_DAY": "PlanDay"}
    index: int
    total_time: int
    total_cost: float
    end_municiplaity_id: int

class PlanPlanDayEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_STARTS_AT_PLAN_DAY"
    source_model: ClassVar[Type[BaseNode]] = PlanNode
    target_model: ClassVar[Type[BaseNode]] = PlanDayNode

class PlanDayPlanDayEdge(BaseEdge):
    label: ClassVar[str] = "NEXT_PLAN_DAY"
    source_model: ClassVar[Type[BaseNode]] = PlanDayNode
    target_model: ClassVar[Type[BaseNode]] = PlanDayNode

class PlanDayGraphRepository(BaseGraphRepository[PlanDayNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PlanDayNode)
from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import  BaseNode

class PlanNode(BaseNode):
    label: ClassVar[str] = "Plan"
    child_relationships = {"PLAN_STARTS_AT_PLAN_DAY": "PlanDay"}
    user_id: int
    no_of_people: int
    start_city_id: int
    end_city_id: int
    max_time_per_day: int = 14*60

class PlanGraphRepository(BaseGraphRepository[PlanNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PlanNode)
from typing import ClassVar
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode


class CityNode(BaseNode):
    label: ClassVar[str] = "City"
    child_relationships = {"CITY_CONTAINS_PLACE": "Place"}
    name: str


class CityGraphRepository(BaseGraphRepository[CityNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CityNode)
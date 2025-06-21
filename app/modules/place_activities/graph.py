from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.activities.graph import ActivityNode
from app.modules.places.graph import PlaceNode


class PlaceActivityEdge(BaseEdge):
    label: ClassVar[str] = "PLACE_HAS_ACTIVITY"
    start_model: ClassVar[Type[BaseNode]] = PlaceNode
    end_model: ClassVar[Type[BaseNode]] = ActivityNode


class PlaceActivityGraphRepository(BaseGraphRepository[PlaceActivityEdge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PlaceActivityEdge)
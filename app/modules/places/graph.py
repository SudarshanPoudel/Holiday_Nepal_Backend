from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.address.graph import MunicipalityNode


class PlaceNode(BaseNode):
    label: ClassVar[str] = "Place"
    name: str
    category: str

class MunicipalityPlaceEdge(BaseEdge):
    label: ClassVar[str] = "MUNICIPALITY_CONTAINS_PLACE"
    source_model: ClassVar[Type[BaseNode]] = MunicipalityNode
    target_model: ClassVar[Type[BaseNode]] = PlaceNode

class PlaceGraphRepository(BaseGraphRepository[PlaceNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PlaceNode)

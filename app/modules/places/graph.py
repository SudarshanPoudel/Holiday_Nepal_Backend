from typing import ClassVar, Type
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.address.graph import MunicipalityNode


class PlaceNode(BaseNode):
    label: ClassVar[str] = "PLACE"
    name: str
    category: str

class MuncipalityPlaceEdge(BaseEdge):
    label: ClassVar[str] = "MUNCIPALITY_CONTAINS_PLACE"
    start_model: ClassVar[Type[BaseNode]] = MunicipalityNode
    end_model: ClassVar[Type[BaseNode]] = PlaceNode
    start_id: int
    end_id: int
    


class PlaceGraphRepository(BaseGraphRepository[PlaceNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PlaceNode)


class MunicipalityPlaceGraphRepository(BaseGraphRepository[MuncipalityPlaceEdge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MuncipalityPlaceEdge)
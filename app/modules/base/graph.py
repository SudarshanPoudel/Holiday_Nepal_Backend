from typing import ClassVar
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode, BaseEdge


class AnyNode(BaseNode):
    pass


class AnyGraphRepository(BaseGraphRepository[AnyNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=AnyNode)
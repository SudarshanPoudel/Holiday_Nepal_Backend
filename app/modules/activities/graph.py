from typing import ClassVar
from neo4j import AsyncSession
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import BaseNode


class ActivityNode(BaseNode):
    label: ClassVar[str] = "Activity"
    name: str

class ActivityGraphRepository(BaseGraphRepository[ActivityNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ActivityNode)



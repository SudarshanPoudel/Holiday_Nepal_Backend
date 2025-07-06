from typing import ClassVar, Type
from app.core.graph_schemas import BaseEdge, BaseNode
from app.modules.activities.graph import ActivityNode
from app.modules.places.graph import PlaceNode


class PlaceActivityEdge(BaseEdge):
    label: ClassVar[str] = "PLACE_HAS_ACTIVITY"
    source_model: ClassVar[Type[BaseNode]] = PlaceNode
    target_model: ClassVar[Type[BaseNode]] = ActivityNode

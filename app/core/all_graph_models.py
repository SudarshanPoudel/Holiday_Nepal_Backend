from app.modules.plan_route_hops.graph import PlanRouteHopNode
from app.modules.places.graph import PlaceNode
from app.modules.plan_day.graph import PlanDayNode
from app.modules.activities.graph import ActivityNode
from app.modules.plan_day_steps.graph import PlanDayStepNode
from app.modules.plans.graph import PlanNode
from app.modules.cities.graph import CityNode

from typing import Type, Optional, Dict
from app.core.graph_schemas import BaseNode
from app.modules.transport_service.graph import TransportServiceNode, TransportServiceRouteHopNode  

# Create a registry
NODE_CLASSES: Dict[str, Type[BaseNode]] = {
    cls.label: cls for cls in [
        PlanRouteHopNode,
        PlaceNode,
        PlanDayNode,
        ActivityNode,
        PlanDayStepNode,
        PlanNode,
        CityNode,
        TransportServiceNode,
        TransportServiceRouteHopNode
    ]
}

def label_to_model(label: str) -> Optional[Type[BaseNode]]:
    """
    Return the node class that matches the given label.
    
    Args:
        label (str): The label to match (e.g., "City")

    Returns:
        Type[BaseNode] or None if not found
    """
    return NODE_CLASSES.get(label)

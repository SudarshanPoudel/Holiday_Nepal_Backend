from app.modules.places.graph import PlaceNode
from app.modules.cities.graph import CityNode

from typing import Type, Optional, Dict
from app.core.graph_schemas import BaseNode

# Create a registry
NODE_CLASSES: Dict[str, Type[BaseNode]] = {
    cls.label: cls for cls in [
        PlaceNode,
        CityNode,
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

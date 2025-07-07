# graph_schema.py
from typing import ClassVar, Tuple, Type, List, Dict
from pydantic import BaseModel, model_validator

from app.utils.helper import symmetric_pair
from typing import ClassVar, Dict
from pydantic import BaseModel

class BaseNode(BaseModel):
    id: int
    label: ClassVar[str] 

    # relationship name -> child label
    child_relationships: ClassVar[Dict[str, str]] = {}
    sequential_child_relationships: ClassVar[Dict[str, str]] = {}

    class Config:
        extra = "forbid"  # forbid unknown fields like label in input

    @property
    def label_name(self) -> str:
        return self.__class__.label


class BaseEdge(BaseModel):
    id: int
    source_id: int
    target_id: int
    label: ClassVar[str]
    source_model: ClassVar[Type["BaseNode"]]
    target_model: ClassVar[Type["BaseNode"]]
    
    @model_validator(mode='before')
    @classmethod
    def infer_id(cls, values: dict) -> dict:
        if "id" not in values or values["id"] is None:
            source = values.get("source_id")
            target = values.get("target_id")
            if source is not None and target is not None:
                # You can implement symmetric_pair or use a simple concatenation
                values["id"] = symmetric_pair(source, target)
        return values
    
    @property
    def label_name(self) -> str:
        return self.__class__.label
    
    class Config:
        extra = "forbid"
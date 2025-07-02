from pyclbr import Class
from typing import ClassVar, Type
from pydantic import BaseModel, model_validator, root_validator

from app.utils.helper import symmetric_pair



class BaseNode(BaseModel):
    id: int
    label: ClassVar[str]  # to be defined in subclass

    class Config:
        extra = "forbid"  # forbid unknown fields like label in input

    @property
    def label(self) -> str:
        return self.__class__.label


class BaseEdge(BaseModel):
    id: int
    start_id: int
    end_id: int

    label: ClassVar[str]
    start_model: ClassVar[Type[BaseNode]]
    end_model: ClassVar[Type[BaseNode]]
    
    @model_validator(mode='before')
    @classmethod
    def infer_id(cls, values: dict) -> dict:
        start = values.get("start_id")
        end = values.get("end_id")
        if start is not None and end is not None:
            values["id"] = symmetric_pair(start, end)
        return values
    
    @property
    def label(self) -> str:
        return self.__class__.label

    class Config:
        extra = "forbid"
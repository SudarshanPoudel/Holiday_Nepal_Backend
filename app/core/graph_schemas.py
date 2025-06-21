from pyclbr import Class
from typing import ClassVar, Type
from pydantic import BaseModel, model_validator



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

    @property
    def label(self) -> str:
        return self.__class__.label

    class Config:
        extra = "forbid"
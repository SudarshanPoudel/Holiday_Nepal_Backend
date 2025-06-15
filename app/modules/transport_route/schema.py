from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.address.schema import MunicipalityBase


class RouteCategoryEnum(str, Enum):
    walking = 'walking'
    road = 'road'
    air = 'air'

class TransportRouteCreate(BaseModel):
    start_municipality_id: int
    end_municipality_id: int
    route_category: RouteCategoryEnum
    distance: float
    average_time: Optional[int]

class TransportRouteUpdate(BaseModel):
    start_municipality_id: Optional[int]
    end_municipality_id: Optional[int]
    route_category: Optional[RouteCategoryEnum]
    distance: Optional[float]
    average_time: Optional[int]

class TransportRouteRead(BaseModel):
    id: int
    start_municipality: MunicipalityBase
    end_municipality: MunicipalityBase
    route_category: RouteCategoryEnum
    distance: float
    average_time: Optional[int]

    class Config:
        from_attributes = True
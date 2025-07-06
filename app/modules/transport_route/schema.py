from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityBase


class RouteCategoryEnum(str, Enum):
    walking = 'walking'
    road = 'road'
    air = 'air'

class TransportRouteCreate(BaseModel):
    start_city_id: int
    end_city_id: int
    route_category: RouteCategoryEnum
    distance: float
    average_duration: Optional[float]
    average_cost: Optional[float]

class TransportRouteReadMinimal(BaseModel):
    id: int
    distance: float
    average_duration: Optional[float]
    start_city_id: int
    end_city_id: int

    class Config:
        from_attributes = True

class TransportRouteRead(BaseModel):
    id: int
    route_category: RouteCategoryEnum
    distance: float
    average_duration: Optional[float]
    start_city: CityBase
    end_city: CityBase

    class Config:
        from_attributes = True
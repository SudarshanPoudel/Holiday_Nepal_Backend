from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityRead


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
    average_cost: Optional[float]
    start_city_id: int
    end_city_id: int

    class Config:
        from_attributes = True

class TransportRouteRead(BaseModel):
    id: int
    route_category: RouteCategoryEnum
    distance: float
    average_duration: Optional[float]
    average_cost: Optional[float]
    start_city: CityRead
    end_city: CityRead

    class Config:
        from_attributes = True
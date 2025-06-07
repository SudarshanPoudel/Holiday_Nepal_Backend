from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.transport_route.schema import RouteCategoryEnum


class TransportServiceCategoryEnum(Enum):
    BUS = 'bus'
    TAXI = 'taxi'
    BIKE = 'bike'
    MINIBUS = 'minibus'
    PLANE = 'plane'
    HELICOPTER = 'helicopter'
    OTHER = 'other'

class TransportServiceCreate(BaseModel):
    route_ids: List[int]
    description: Optional[str]
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    average_time: Optional[int]

class TransportServiceBase(BaseModel):
    service_provider_id: int
    start_municipality_id: int
    end_municipality_id: int
    description: Optional[str]
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    total_distance: float
    average_time: Optional[int]

class TransportServiceUpdate(BaseModel):
    service_provider_id: Optional[int]
    description: Optional[str]
    route_category: Optional[RouteCategoryEnum]
    transport_category: Optional[TransportServiceCategoryEnum]
    average_time: Optional[int]
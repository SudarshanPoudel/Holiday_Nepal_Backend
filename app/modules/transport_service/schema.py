from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityRead
from app.modules.storage.schema import ImageRead
from app.modules.transport_route.schema import RouteCategoryEnum, TransportRouteRead


class TransportServiceCategoryEnum(str, Enum):
    bus = 'bus'
    taxi = 'taxi'
    bike = 'bike'
    minibus = 'minibus'
    jeep = 'jeep'
    plane = 'plane'
    helicopter = 'helicopter'
    other = 'other'


class TransportServiceCreate(BaseModel):
    route_ids: List[int]
    description: Optional[str]
    image_ids: Optional[List[int]] = None  
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    average_duration: Optional[float]
    cost: Optional[float]
    contact: Optional[str] = None

class TransportServiceBase(BaseModel):
    start_city_id: int
    end_city_id: int
    description: Optional[str]
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    average_duration: Optional[float]
    total_distance: float
    cost: Optional[float]
    contact: Optional[str] = None

class TransportServiceRouteSegmentRead(BaseModel):
    id: int
    index: int
    route: TransportRouteRead


class TransportServiceReadAll(BaseModel):
    id: int
    start_city: CityRead
    end_city: CityRead
    description: Optional[str]
    images: List[ImageRead] 
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    total_distance: float
    average_duration: Optional[float]
    cost: Optional[float]
    contact: Optional[str] = None


class TransportServiceRead(TransportServiceReadAll):
    description: Optional[str]
    route_segments: List[TransportServiceRouteSegmentRead]

class TransportServiceFilters(BaseModel):
    start_city_id: Optional[int] = None
    end_city_id: Optional[int] = None
    route_category: Optional[RouteCategoryEnum] = None
    transport_category: Optional[TransportServiceCategoryEnum] = None
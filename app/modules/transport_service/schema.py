from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.address.schema import MunicipalityBase
from app.modules.storage.schema import ImageRead
from app.modules.transport_route.schema import RouteCategoryEnum, TransportRouteRead


class TransportServiceCategoryEnum(str, Enum):
    bus = 'bus'
    taxi = 'taxi'
    bike = 'bike'
    minibus = 'minibus'
    plane = 'plane'
    helicopter = 'helicopter'
    other = 'other'


class TransportServiceCreate(BaseModel):
    route_ids: List[int]
    description: Optional[str]
    image_ids: Optional[List[int]] = None  
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    average_duration: Optional[int]


class TransportServiceBase(BaseModel):
    service_provider_id: int
    start_municipality_id: int
    end_municipality_id: int
    description: Optional[str]
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    average_duration: Optional[int]
    total_distance: float


class TransportServiceRouteSegmentRead(BaseModel):
    id: int
    index: int
    route: TransportRouteRead


class TransportServiceReadAll(BaseModel):
    id: int
    service_provider_id: int
    start_municipality: MunicipalityBase
    end_municipality: MunicipalityBase
    images: List[ImageRead] 
    route_category: RouteCategoryEnum
    transport_category: TransportServiceCategoryEnum
    total_distance: float
    average_duration: Optional[int]


class TransportServiceRead(TransportServiceReadAll):
    description: Optional[str]
    route_segments: List[TransportServiceRouteSegmentRead]


class TransportServiceUpdate(BaseModel):
    service_provider_id: Optional[int]
    description: Optional[str]
    route_category: Optional[RouteCategoryEnum]
    transport_category: Optional[TransportServiceCategoryEnum]
    average_duration: Optional[int]
    image_ids: Optional[List[int]] = None  


class TransportServiceFilters(BaseModel):
    service_provider_id: Optional[int] = None
    start_municipality_id: Optional[int] = None
    end_municipality_id: Optional[int] = None
    route_category: Optional[RouteCategoryEnum] = None
    transport_category: Optional[TransportServiceCategoryEnum] = None
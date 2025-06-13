from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.storage.schema import ImageRead

class AccomodationCategoryEnum(Enum):
    HOTEL = 'hotel'
    MOTEL = 'motel'
    RESORT = 'resort'
    HOSTEL = 'hostel'
    HOMESTAY = 'homestay'
    OTHER = 'other'

class AccomodationServiceCreate(BaseModel):
    description: Optional[str] = None
    municipality_id: int
    full_location: str
    accomodation_category: AccomodationCategoryEnum
    longitude: float
    latitude: float
    cost_per_night: float
    image_ids: Optional[List[int]]

class AccomodationServiceCreateInternal(BaseModel):
    service_provider_id: int
    description: Optional[str] = None
    municipality_id: int
    full_location: str
    accomodation_category: AccomodationCategoryEnum
    longitude: float
    latitude: float
    cost_per_night: float

class AccomodationServiceUpdate(BaseModel):
    description: Optional[str] = None
    service_provider_id: Optional[int] = None
    municipality_id: Optional[int] = None
    full_location: Optional[str] = None
    accomodation_category: Optional[AccomodationCategoryEnum] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    cost_per_night: Optional[float] = None
    image_ids: Optional[List[int]]

class AccomodationServiceUpdateInternal(BaseModel):
    description: Optional[str] = None
    municipality_id: Optional[int] = None
    full_location: Optional[str] = None
    accomodation_category: Optional[AccomodationCategoryEnum] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    cost_per_night: Optional[float] = None

class AccomodationServiceRead(BaseModel):
    id: int
    description: Optional[str] = None
    service_provider_id: int
    municipality_id: int
    full_location: str
    accomodation_category: AccomodationCategoryEnum
    longitude: float
    latitude: float
    cost_per_night: float
    images: List[ImageRead]

    class Config:
        from_attributes = True
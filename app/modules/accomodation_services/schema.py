from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityRead
from app.modules.storage.schema import ImageRead

class AccomodationCategoryEnum(str, Enum):
    hotel = 'hotel'
    motel = 'motel'
    resort = 'resort'
    hostel = 'hostel'
    homestay = 'homestay'
    other = 'other'

class AccomodationServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    city_id: int
    full_address: str
    accomodation_category: AccomodationCategoryEnum
    longitude: float
    latitude: float
    cost_per_night: float

class AccomodationServiceCreate(AccomodationServiceBase):
    image_ids: Optional[List[int]]


class AccomodationServiceReadMinimal(BaseModel):
    id: int
    name: str
    full_address: str
    city_id: int
    accomodation_category: AccomodationCategoryEnum
    longitude: float
    latitude: float
    cost_per_night: float

    class Config:
        from_attributes = True


class AccomodationServiceRead(AccomodationServiceReadMinimal):
    description: Optional[str] = None
    images: List[ImageRead]

    class Config:
        from_attributes = True

class AccomodationServiceFilter(BaseModel):
    city_id: Optional[int] = None
    accomodation_category: Optional[AccomodationCategoryEnum] = None

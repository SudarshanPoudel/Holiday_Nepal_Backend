from typing import ClassVar, List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityBase
from app.modules.place_activities.schema import PlaceActivityCreate,  PlaceActivityRead
from app.modules.storage.schema import ImageRead

class PlaceCategoryEnum(str, Enum):
    natural = "natural"
    cultural = "cultural"
    historic = "historic"
    religious = "religious"
    adventure = "adventure"
    wildlife = "wildlife"
    educational = "educational"
    architectural = "architectural"
    other = "other"

class PlaceBase(BaseModel):
    name: str
    category: PlaceCategoryEnum
    longitude: float
    latitude: float
    description: Optional[str] 
    city_id: Optional[int] 

    class Config:
        use_enum_values = True


class PlaceCreate(PlaceBase):
    activities: Optional[List[PlaceActivityCreate]] 
    image_ids: Optional[list[int]] 


class PlaceReadBasic(BaseModel):
    id: int
    name: str
    longitude: float
    latitude: float
    category: PlaceCategoryEnum

class PlaceRead(BaseModel):
    id: int
    name: str
    longitude: float
    latitude: float
    category: PlaceCategoryEnum
    description: Optional[str]
    images: Optional[list[ImageRead]]
    place_activities: Optional[List[PlaceActivityRead]]
    city: Optional[CityBase]
    
    class Config:
        from_attributes = True

class PlaceFilters(BaseModel):
    city_id: Optional[int] = None
from typing import ClassVar, List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.cities.schema import CityRead
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
    categories: List[PlaceCategoryEnum]
    longitude: float
    latitude: float
    description: Optional[str] 
    city_id: Optional[int] 
    average_visit_duration: Optional[float]
    average_visit_cost: Optional[float]

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
    categories: List[PlaceCategoryEnum]
    average_visit_duration: Optional[float]
    average_visit_cost: Optional[float]

class PlaceRead(BaseModel):
    id: int
    name: str
    longitude: float
    latitude: float
    categories: List[PlaceCategoryEnum]
    description: Optional[str]
    average_visit_duration: Optional[float]
    average_visit_cost: Optional[float]
    images: Optional[list[ImageRead]]
    place_activities: Optional[List[PlaceActivityRead]]
    city: Optional[CityRead]
    
    class Config:
        from_attributes = True

class PlaceFilters(BaseModel):
    city_id: Optional[int] = None
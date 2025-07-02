from typing import ClassVar, List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.address.schema import MunicipalityBase
from app.modules.place_activities.schema import PlaceActivityCreate, PlaceActivityCreateInternal, PlaceActivityRead, PlaceActivityUpdate
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

class CreatePlace(BaseModel):
    name: str
    category: PlaceCategoryEnum
    longitude: float
    latitude: float
    description: Optional[str] 
    activities: Optional[List[PlaceActivityCreate]] 
    image_ids: Optional[list[int]] 
    municipality_id: Optional[int] 

    class Config:
        use_enum_values = True

class CreatePlaceInternal(BaseModel):
    name: str
    category: PlaceCategoryEnum
    longitude: float
    latitude: float
    description: Optional[str] 
    municipality_id: Optional[int] 

    class Config:
        use_enum_values = True

class UpdatePlace(BaseModel):
    name: Optional[str] 
    category: Optional[PlaceCategoryEnum]
    longitude: Optional[float] 
    latitude: Optional[float] 
    description: Optional[str] 
    municipality_id: Optional[int] 
    activities: Optional[List[PlaceActivityCreate]] 
    image_ids: Optional[list[int]] 


class UpdatePlaceInternal(BaseModel):
    name: Optional[str] 
    category: Optional[PlaceCategoryEnum]
    longitude: Optional[float] 
    latitude: Optional[float] 
    description: Optional[str] 
    municipality_id: Optional[int] 

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
    activities: Optional[List[PlaceActivityRead]]
    municipality: Optional[MunicipalityBase]

    @classmethod
    def from_model(cls, place):
        return cls(
            id=place.id,
            name=place.name,
            latitude=place.latitude,
            longitude=place.longitude,
            description=place.description,
            category=place.category,
            images=[ImageRead.model_validate(img, from_attributes=True) for img in place.images],
            activities=[
                PlaceActivityRead.model_validate(pa, from_attributes=True)
                for pa in place.place_activities
            ],
            municipality=MunicipalityBase.model_validate(place.municipality, from_attributes=True)
        )


class PlaceFilters(BaseModel):
    municipality_id: Optional[int] = None
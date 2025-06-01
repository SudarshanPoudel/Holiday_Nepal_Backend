from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.activities.schema import ReadActivity
from app.modules.place_activities.schema import CreatePlaceActivity, CreatePlaceActivityInternal, ReadPlaceActivity, UpdatePlaceActivity
from app.modules.places.models import Place
from app.modules.storage.schema import ReadImage


class PlaceCategoryEnum(Enum):
    NATURAL = "natural"
    CULTURAL = "cultural"
    HISTORICAL = "historical"
    RELIGIOUS = "religious"
    ADVENTURE = "adventure"
    WILDLIFE = "wildlife"
    EDUCATIONAL = "educational"
    ARCHITECTURAL = "architectural"
    OTHER = "other"


class CreatePlace(BaseModel):
    name: str
    categories: List[PlaceCategoryEnum]
    longitude: float
    latitude: float
    description: Optional[str] = None
    activities: Optional[List[CreatePlaceActivity]] = None
    image_ids: Optional[list[int]] = None

    class Config:
        use_enum_values = True

class CreatePlaceInternal(BaseModel):
    name: str
    categories: List[PlaceCategoryEnum]
    longitude: float
    latitude: float
    description: Optional[str] = None

    class Config:
        use_enum_values = True

class UpdatePlace(BaseModel):
    name: Optional[str] = None
    categories: Optional[List[PlaceCategoryEnum]] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    description: Optional[str] = None
    activities: Optional[List[UpdatePlaceActivity]] = None
    image_ids: Optional[list[int]] = None

class UpdatePlaceInternal(BaseModel):
    name: Optional[str] = None
    categories: Optional[List[PlaceCategoryEnum]] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    description: Optional[str] = None

class ReadPlace(BaseModel):
    id: int
    name: str
    longitude: float
    latitude: float
    categories: List[PlaceCategoryEnum]
    description: Optional[str] = None
    images: Optional[list[ReadImage]] = None
    activities: Optional[List[ReadPlaceActivity]] = None

    @classmethod
    def from_model(cls, place: Place):
        return cls(
            id=place.id,
            name=place.name,
            latitude=place.latitude,
            longitude=place.longitude,
            description=place.description,
            categories=place.categories,
            images=[ReadImage.model_validate(img, from_attributes=True) for img in place.images],
            activities=[
                ReadPlaceActivity.model_validate(pa, from_attributes=True)
                for pa in place.place_activities
            ]
        )


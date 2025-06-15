from typing import Optional
from pydantic import BaseModel
from enum import Enum

class ImageCategoryEnum(str, Enum):
    user_profile = "user_profile"
    place = "place"
    activities = "activities"
    services = "services"
    other = "other"

class ImageRead(BaseModel):
    id: int
    key: str
    url: str

    class Config:
        from_attributes = True

class ImageCreate(BaseModel):
    key: str
    url: str
    category: ImageCategoryEnum
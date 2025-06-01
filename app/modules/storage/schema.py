from typing import Optional
from pydantic import BaseModel
from enum import Enum

class ImageCategoryEnum(str, Enum):
    USER_PROFILE = "user_profile"
    PLACE = "place"
    ACTIVITIES = "activities"
    SERVICES = "services"
    OTHER = "other"

class ReadImage(BaseModel):
    id: int
    key: str
    url: str

    class Config:
        from_attributes = True

class CreateImage(BaseModel):
    key: str
    url: str
    category: ImageCategoryEnum
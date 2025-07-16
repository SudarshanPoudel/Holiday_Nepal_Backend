from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from enum import Enum

from app.core.config import settings

class ImageCategoryEnum(str, Enum):
    user_profile = "user_profile"
    place = "place"
    activities = "activities"
    services = "services"
    other = "other"

def generate_url_from_key(key: str) -> str:
    return f"http://localhost:4566/{settings.AWS_STORAGE_BUCKET_NAME}/{key}"


class ImageRead(BaseModel):
    id: int
    key: str = Field(exclude=True) # <-- Required to compute URL
    url: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True

    @field_serializer("url", when_used="always")
    def compute_url(self, value, info):
        return generate_url_from_key(self.key)


class ImageCreate(BaseModel):
    key: str
    category: ImageCategoryEnum
from typing import Optional
from pydantic import BaseModel

from app.modules.storage.schema import ReadImage


class CreateActivity(BaseModel):
    name: str
    image_id: int
    description: Optional[str] = None

class CreateActivityInternal(CreateActivity):
    name_slug: str

class UpdateActivity(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None

class UpdateActivityInternal(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    name_slug: Optional[str] = None


class ReadActivity(BaseModel):
    id: int
    name: str
    name_slug: str
    description: Optional[str] = None
    image: ReadImage = None

    class Config:
        from_attributes = True

    
from typing import Optional
from pydantic import BaseModel

from app.modules.storage.schema import ImageRead


class ActivityCreate(BaseModel):
    name: str
    image_id: int
    description: Optional[str] = None

class ActivityCreateInternal(ActivityCreate):
    name_slug: str

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ActivityUpdateInternal(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    name_slug: Optional[str] = None


class ActivityRead(BaseModel):
    id: int
    name: str
    name_slug: str
    description: Optional[str] = None
    image: ImageRead = None

    class Config:
        from_attributes = True

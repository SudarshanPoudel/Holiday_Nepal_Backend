from typing import List, Optional
from pydantic import BaseModel

from app.modules.places.schema import PlaceRead
from app.modules.storage.schema import ImageRead


class ActivityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_id: int

class ActivityReadMinimal(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActivityRead(ActivityReadMinimal):
    description: Optional[str] = None
    image: ImageRead = None

    class Config:
        from_attributes = True


class ActivityReadWithImage(ActivityReadMinimal):
    image: Optional[ImageRead] = None

class ActivityReadFull(ActivityRead):
    # places: Optional[List[PlaceRead]] = None
    pass

from typing import Optional
from pydantic import BaseModel

from app.modules.activities.schema import ActivityReadWithImage
from app.modules.storage.schema import ImageRead

class PlaceActivityCreate(BaseModel):
    activity_id: int
    title: str
    description: Optional[str] = None
    average_duration: Optional[float] = None
    average_cost: Optional[float] = None

class PlaceActivityBase(PlaceActivityCreate):
    place_id: int

class PlaceActivityRead(BaseModel):
    id: int
    title: str
    place_id: int
    description: Optional[str] = None
    average_duration: Optional[float] = None
    average_cost: Optional[float] = None

    activity : ActivityReadWithImage
    
    class Config:
        from_attributes = True
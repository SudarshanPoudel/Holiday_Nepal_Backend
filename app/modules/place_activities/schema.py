from typing import Optional
from pydantic import BaseModel

from app.modules.activities.schema import ReadActivity

class CreatePlaceActivity(BaseModel):
    activity_id: int
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None

class CreatePlaceActivityInternal(CreatePlaceActivity):
    place_id: int

class UpdatePlaceActivity(BaseModel):
    id: int
    activity_id: Optional[int] = None
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None

class UpdatePlaceActivityInternal(UpdatePlaceActivity):
    place_id: int

class ReadPlaceActivity(BaseModel):
    id: int
    activity : ReadActivity
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None
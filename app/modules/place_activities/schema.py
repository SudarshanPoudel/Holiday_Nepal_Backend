from typing import Optional
from pydantic import BaseModel

class PlaceActivityCreate(BaseModel):
    activity_id: int
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None

class PlaceActivityCreateInternal(PlaceActivityCreate):
    place_id: int

class PlaceActivityUpdate(BaseModel):
    activity_id: Optional[int] = None
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None

class PlaceActivityUpdateInternal(PlaceActivityUpdate):
    place_id: int

class BaseActivity(BaseModel):
    id: int
    name: str

class PlaceActivityRead(BaseModel):
    activity : BaseActivity
    description: Optional[str] = None
    average_duration: Optional[int] = None
    average_cost: Optional[float] = None
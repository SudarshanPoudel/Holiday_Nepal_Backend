from typing import Any, Optional
from pydantic import BaseModel

class CityCreate(BaseModel):
    name: str
    latitude: float
    longitude: float

class CityRead(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True

class CityNearest(CityRead):
    distance: Optional[float]

    class Config:
        from_attributes = True
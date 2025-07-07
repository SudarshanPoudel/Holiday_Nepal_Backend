from typing import Optional
from pydantic import BaseModel

class CityCreate(BaseModel):
    name: str
    latitude: float
    longitude: float

class CityBase(BaseModel):
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True

class CityNearest(CityBase):
    distance: Optional[float]

    class Config:
        from_attributes = True
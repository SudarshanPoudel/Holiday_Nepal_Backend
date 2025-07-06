from typing import Optional
from pydantic import BaseModel



class CityBase(BaseModel):
    id: Optional[int] = None
    name: str
    longitude: float
    latitude: float

    class Config:
        from_attributes = True

class CityNearest(CityBase):
    distance: Optional[float]

    class Config:
        from_attributes = True
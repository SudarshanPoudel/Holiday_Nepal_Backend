from typing import Optional
from pydantic import BaseModel


class DistrictBase(BaseModel):
    id: Optional[int] = None
    name: str
    headquarter: str

    class Config:
        from_attributes = True

class MunicipalityBase(BaseModel):
    id: Optional[int] = None
    name: str
    district_id: int
    longitude: float
    latitude: float

    class Config:
        from_attributes = True

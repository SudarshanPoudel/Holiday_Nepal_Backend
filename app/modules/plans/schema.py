from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel
from sympy import Union

from app.modules.cities.schema import CityRead
from app.modules.plan_day.schema import PlanDayRead
from app.modules.storage.schema import ImageRead
from app.modules.users.schemas import UserReadMinimal

class PlanCreate(BaseModel):
    title: str
    description: Optional[str]
    start_city_id: Optional[int] = None
    no_of_people: int = 1
    image_id: Optional[int] = None
    is_private: bool = False

class PlanBase(PlanCreate):
    user_id: int
    estimated_cost: Optional[float] = 0.0
    no_of_days: Optional[int] = 0

class PlanIndex(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_cost: Optional[float]
    no_of_days: int
    no_of_people: int
    rating: Optional[float]
    vote_count: Optional[int]
    is_saved: Optional[bool] = None
    self_rating: Optional[int] = None

    # created_at: datetime
    # updated_at: datetime
    
    image: Optional[ImageRead] 
    start_city: Optional[CityRead]
    user: UserReadMinimal

    class Config:
        from_attributes = True


class PlanRead(PlanIndex):
    is_private: bool
    days: List[PlanDayRead] = []

    is_saved: Optional[bool] = None
    self_rating: Optional[int] = None
    

    class Config:
        from_attributes = True

class PlanFilters(BaseModel):
    no_of_days: Optional[int] = None
    no_of_people: Optional[int] = None
    start_city_id: Optional[int] = None
    user_id: Optional[int] = None

class PlanFiltersInternal(PlanFilters):
    is_private: bool = False
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.modules.cities.schema import CityRead
from app.modules.plan_day.schema import PlanDayRead
from app.modules.users.schemas import UserRead

class PlanCreate(BaseModel):
    title: str
    description: Optional[str]
    start_city_id: int
    no_of_people: int = 1
    is_private: bool = True

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
    created_at: datetime
    updated_at: datetime
    
    start_city: CityRead
    user: UserRead

    class Config:
        from_attributes = True
        
class PlanRead(PlanIndex):
    is_private: bool
    days: List[PlanDayRead]

    class Config:
        from_attributes = True

class PlanFilters(BaseModel):
    no_of_days: Optional[int] = None
    no_of_people: Optional[int] = None
    start_city_id: Optional[int] = None

class PlanFiltersInternal(PlanFilters):
    is_private: bool = False
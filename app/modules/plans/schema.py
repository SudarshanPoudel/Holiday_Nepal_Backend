from typing import Optional, List
from pydantic import BaseModel

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

class PlanRead(BaseModel):
    id: int
    title: str
    desciption: Optional[str] = None
    estimated_cost: Optional[float] = 0.0
    no_of_days: int
    no_of_people: int
    rating: Optional[float] = 0.0
    vote_count: Optional[int] = 0
    start_city_id: int
    is_private: bool

    days: List[PlanDayRead]
    user: UserRead

    class Config:
        from_attributes = True
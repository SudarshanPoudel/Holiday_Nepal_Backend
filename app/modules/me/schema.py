from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.modules.cities.schema import CityRead
from app.modules.storage.schema import ImageRead
from app.modules.users.schemas import UserPlanRatingRead, UserPlanRead


class MeRead(BaseModel):
    id: Optional[int]
    username: str
    email: EmailStr
    no_of_plans: Optional[int] = 0
    
    city: Optional[CityRead]
    image: Optional[ImageRead]
    plans: List[UserPlanRead]
    saved_plans: List[UserPlanRead]


class MeUpdate(BaseModel):
    username: Optional[str]
    image_id: Optional[int]
    city_id: Optional[int]
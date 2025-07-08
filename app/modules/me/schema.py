from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.modules.storage.schema import ImageRead
from app.modules.users.schemas import UserPlanRatingRead, UserPlanRead


class MeRead(BaseModel):
    id: Optional[int]
    username: str
    email: EmailStr

    image: Optional[ImageRead]
    plans: List[UserPlanRead]
    saved_plans: List[UserPlanRead]
    plan_ratings: List[UserPlanRatingRead]
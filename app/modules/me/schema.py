from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.modules.activities.schema import ActivityReadMinimal
from app.modules.cities.schema import CityRead
from app.modules.places.schema import PlaceCategoryEnum
from app.modules.storage.schema import ImageRead
from app.modules.users.schemas import DistancePreferenceEnum, UserPlanRatingRead, UserPlanRead


class MeRead(BaseModel):
    id: Optional[int]
    username: str
    email: EmailStr
    prefer_place_categories: Optional[List[PlaceCategoryEnum]]
    prefer_travel_distance: Optional[DistancePreferenceEnum]
    additional_preferences: Optional[str]
    no_of_plans: Optional[int] = 0
    
    city: Optional[CityRead]
    image: Optional[ImageRead]
    plans: List[UserPlanRead]
    saved_plans: List[UserPlanRead]
    prefer_activities: List[ActivityReadMinimal]

class MeUpdateInternal(BaseModel):
    username: Optional[str]
    image_id: Optional[int]
    city_id: Optional[int]
    prefer_place_categories: Optional[List[PlaceCategoryEnum]]
    prefer_travel_distance: Optional[DistancePreferenceEnum]
    additional_preferences: Optional[str]

class MeUpdate(MeUpdateInternal):
    prefer_activities: Optional[List[int]]

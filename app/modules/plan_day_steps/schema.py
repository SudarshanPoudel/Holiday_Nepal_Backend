from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.activities.schema import ActivityRead, ActivityReadWithImage
from app.modules.cities.schema import CityRead
from app.modules.place_activities.schema import PlaceActivityRead
from app.modules.places.schema import  PlaceReadBasic
from app.modules.plan_route_hops.schema import PlanRouteHopRead
from app.modules.storage.schema import ImageRead

class PlanDayTimeFrameEnum(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"
    full_day = "full_day"

class PlanDayStepCategoryEnum(str, Enum):
    visit = "visit"
    activity = "activity"
    transport = "transport"

class PlanDayStepRead(BaseModel):
    id: int
    index: int
    title: str
    time_frame: PlanDayTimeFrameEnum
    category: PlanDayStepCategoryEnum
    cost: float
    
    image: ImageRead
    place_activity: Optional[PlaceActivityRead]
    place: Optional[PlaceReadBasic]
    city_start: Optional[CityRead]
    city_end: Optional[CityRead]
    route_hops: Optional[List[PlanRouteHopRead]]
    
class PlanDayStepCreate(BaseModel):
    plan_id: int
    category: PlanDayStepCategoryEnum
    place_id: Optional[int] = None
    end_city_id: Optional[int] = None
    place_activity_id: Optional[int] = None

class PlanDayStepCreateInternal(BaseModel):
    plan_day_id: int
    index: int
    title: str
    category: PlanDayStepCategoryEnum
    time_frame: PlanDayTimeFrameEnum
    start_city_id: Optional[int] = None
    duration: float
    cost: float
    image_id: int
    place_id: Optional[int] = None
    start_city_id: Optional[int] = None
    end_city_id: Optional[int] = None
    place_activity_id: Optional[int] = None
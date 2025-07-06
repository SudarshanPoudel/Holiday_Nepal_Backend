from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.activities.schema import ActivityRead
from app.modules.address.schema import MunicipalityBase
from app.modules.places.schema import  PlaceReadBasic
from app.modules.plan_route_hops.schema import PlanRouteHopRead
from app.modules.storage.schema import ImageRead

class PlanDayTimeFrameEnum(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"
    full_day = "full day"

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
    
    image: ImageRead
    activities: List[ActivityRead]
    place: Optional[PlaceReadBasic]
    municipality_start: Optional[MunicipalityBase]
    municipality_end: Optional[MunicipalityBase]
    route_hops: Optional[List[PlanRouteHopRead]]
    
class PlanDayStepCreate(BaseModel):
    plan_id: int
    category: PlanDayStepCategoryEnum
    place_id: Optional[int] = None
    end_municipality_id: Optional[int] = None
    place_activity_id: Optional[int] = None

class PlanDayStepCreateInternal(BaseModel):
    plan_day_id: int
    index: int
    title: str
    category: PlanDayStepCategoryEnum
    time_frame: PlanDayTimeFrameEnum
    start_municipality_id: Optional[int] = None
    duration: float
    cost: float
    image_id: int
    place_id: Optional[int] = None
    start_municipality_id: Optional[int] = None
    end_municipality_id: Optional[int] = None
    place_activity_id: Optional[int] = None
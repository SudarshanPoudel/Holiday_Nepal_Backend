from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.modules.activities.schema import ActivityRead
from app.modules.address.schema import MunicipalityBase
from app.modules.places.schema import  PlaceReadBasic
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
    title: str
    time_frame: PlanDayTimeFrameEnum
    category: PlanDayStepCategoryEnum
    
    image: ImageRead
    activities: List[ActivityRead]
    place: Optional[PlaceReadBasic]
    municipality_start: Optional[MunicipalityBase]
    municipality_end: Optional[MunicipalityBase]
    
class PlanDayStepCreate(BaseModel):
    category: PlanDayStepCategoryEnum
    place_id: int # Pass end municipality id, or place to visit

class PlanDayStepCreateInternal(BaseModel):
    plan_day_id: int
    title: str
    category: PlanDayStepCategoryEnum
    time_frame: PlanDayTimeFrameEnum
    duration: float
    image_id: int
    place_id: Optional[int] = None
    municipality_start_id: Optional[int] = None
    municipality_end_id: Optional[int] = None
from typing import List, Optional
from pydantic import BaseModel

from app.modules.plan_day_steps.schema import PlanDayStepRead

class PlanDayRead(BaseModel):
    id: int
    index: int
    title: str
    can_delete: Optional[bool] = True

    steps: List[PlanDayStepRead] = []

class PlanDayCreate(BaseModel):
    plan_id: int
    title: str
    next_plan_day_id: Optional[int] = None

class PlanDayUpdate(BaseModel):
    title: Optional[str]

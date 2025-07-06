from typing import List
from pydantic import BaseModel

from app.modules.plan_day_steps.schema import PlanDayStepRead

class PlanDayRead(BaseModel):
    id: int
    index: int
    title: str

    steps: List[PlanDayStepRead]

class PlanDayCreate(BaseModel):
    plan_id: int
    index: int
    title: str

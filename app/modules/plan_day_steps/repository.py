from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.plan_day_steps.schema import PlanDayStepRead

class PlanDayStepRepositary(BaseRepository[PlanDayStep, PlanDayStepRead]):
    def __init__(self, db):
        super().__init__(PlanDayStep, db)

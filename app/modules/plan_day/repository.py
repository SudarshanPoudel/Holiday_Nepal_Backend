from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day.models import PlanDay


class PlanDayRepository(BaseRepository[PlanDay, PlanDayCreate]):
    def __init__(self, db):
        super().__init__(PlanDay, db)
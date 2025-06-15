from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_day.schema import PlanDayRead
from app.modules.plan_day.models import PlanDay


class PlanDayRepository(BaseRepository[PlanDay, PlanDayRead]):
    def __init__(self, db):
        super().__init__(PlanDay, db)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plans.models import Plan
from app.modules.plans.schema import PlanRead

class PlanRepository(BaseRepository[Plan, PlanRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plan, db)
        
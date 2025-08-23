from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_route_hops.models import PlanRouteHop
from app.modules.plan_route_hops.schema import PlanRouteHopCreate

class PlanRouteHopsRepository(BaseRepository[PlanRouteHop, PlanRouteHopCreate]):
    def __init__(self, db):
        super().__init__(PlanRouteHop, db)

    async def clear_all(self, plan_day_step_id: int):
        await self.db.execute(delete(PlanRouteHop).where(PlanRouteHop.plan_day_step_id == plan_day_step_id))
        await self.db.commit()
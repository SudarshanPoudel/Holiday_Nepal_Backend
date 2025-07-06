from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_route_hops.models import PlanRouteHop
from app.modules.plan_route_hops.schema import PlanRouteHopCreate

class PlanRouteHopsRepository(BaseRepository[PlanRouteHop, PlanRouteHopCreate]):
    def __init__(self, db):
        super().__init__(PlanRouteHop, db)
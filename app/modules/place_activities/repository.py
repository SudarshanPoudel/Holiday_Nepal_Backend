import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.activities.models import Activity
from app.modules.activities.schema import ActivityRead
from app.modules.place_activities.models import PlaceActivity
from app.modules.place_activities.schema import PlaceActivityBase

class PlaceActivityRepository(BaseRepository[PlaceActivity, PlaceActivityBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(PlaceActivity, db)

    async def clear_place_activities(self, place_id: int):
        await self.db.execute(delete(PlaceActivity).where(PlaceActivity.place_id == place_id))
        await self.db.commit()

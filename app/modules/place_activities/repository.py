from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.activities.models import Activity
from app.modules.activities.schema import ActivityRead
from app.modules.place_activities.models import PlaceActivity
from app.modules.place_activities.schema import PlaceActivityRead

class PlaceActivityRepository(BaseRepository[PlaceActivity, PlaceActivityRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(PlaceActivity, db)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.activities.models import Activity
from app.modules.activities.schema import ReadActivity

class ActivityRepository(BaseRepository[Activity, ReadActivity]):
    def __init__(self, db: AsyncSession):
        super().__init__(Activity, db)
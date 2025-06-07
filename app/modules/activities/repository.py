from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.activities.models import Activity
from app.modules.activities.schema import ActivityRead

class ActivityRepository(BaseRepository[Activity, ActivityRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Activity, db)
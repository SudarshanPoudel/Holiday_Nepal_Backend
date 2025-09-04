from typing import List
from sqlalchemy import delete, func, insert, select
from app.core.repository import BaseRepository
from app.modules.plans.models import Plan
from app.modules.users.models import User, user_prefer_place_activities
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.schemas import UserCreate


class UserRepository(BaseRepository[User, UserCreate]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_no_of_plans(self, user_id: int, include_private: bool = False) -> int:
        stmt = select(func.count(Plan.id)).where(Plan.user_id == user_id)

        if not include_private:
            stmt = stmt.where(Plan.is_private == False)

        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def update_prefer_activities(self, user_id: int, activities: List[int]):
        delete_stmt = delete(user_prefer_place_activities).where(user_prefer_place_activities.c.user_id == user_id)
        await self.db.execute(delete_stmt)
        if activities:
            values = [{"user_id": user_id, "activities_id": act_id} for act_id in activities]
            await self.db.execute(insert(user_prefer_place_activities).values(values))
        await self.db.commit()
from sqlalchemy import func, select
from app.core.repository import BaseRepository
from app.modules.plans.models import Plan
from app.modules.users.models import User
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
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.me.schema import MeRead
from app.modules.users.repository import UserRepository


class MeController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.db = db
        self.user_repository = UserRepository(db)

    async def me(self):
        user = await self.user_repository.get(
            self.user_id,
            load_relations=["image", "city", "plans.start_city", "plan.image", "saved_plans.start_city", "plan_ratings.plan.start_city", "plan_ratings.plan.image"]
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return BaseResponse(message="Profile fetched  success", data=MeRead.model_validate(user, from_attributes=True))
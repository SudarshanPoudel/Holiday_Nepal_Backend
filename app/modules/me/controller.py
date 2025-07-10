from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.me.schema import MeRead, MeUpdate
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserUpdate


class MeController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.db = db
        self.user_repository = UserRepository(db)

    async def me(self):
        user = await self.user_repository.get(
            self.user_id,
            load_relations=["image", "city", "plans.start_city", "plans.image", "saved_plans.start_city", "plan_ratings.plan.start_city", "plan_ratings.plan.image"]
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        data = MeRead.model_validate(user, from_attributes=True)
        data.no_of_plans = await self.user_repository.get_no_of_plans(self.user_id, include_private=True)
        return BaseResponse(message="Profile fetched  success", data=data)
    
    async def update_me(self, profile_info: MeUpdate):
        user = await self.user_repository.get(self.user_id)
        if user.username != profile_info.username:
            existing = await self.user_repository.get_all_filtered(filters={"username": profile_info.username})
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
        updated_user = await self.user_repository.update(self.user_id, profile_info)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return BaseResponse(message="Profile updated successfully", data={"id": updated_user.id, "username": updated_user.username, "image_id": updated_user.image_id})
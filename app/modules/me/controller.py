from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.me.schema import MeRead, MeUpdate, MeUpdateInternal
from app.modules.users.repository import UserRepository


class MeController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.db = db
        self.user_repository = UserRepository(db)

    async def me(self):
        user = await self.user_repository.get(
            self.user_id,
            load_relations=["image", "city", "prefer_activities"]
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
            if existing and existing[0].id != self.user_id:
                raise HTTPException(status_code=400, detail="Username already exists")
        profile_info_internal = MeUpdateInternal(**profile_info.model_dump(exclude=["prefer_activities"]))
        updated_user = await self.user_repository.update(self.user_id, profile_info_internal)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        if profile_info.prefer_activities:
            await self.user_repository.update_prefer_activities(self.user_id, profile_info.prefer_activities)

        user = await self.user_repository.get(
            self.user_id,
            load_relations=["image", "city", "prefer_activities"]
        )
        data = MeRead.model_validate(user, from_attributes=True)
        data.no_of_plans = await self.user_repository.get_no_of_plans(self.user_id, include_private=True)

        return BaseResponse(message="Profile updated successfully", data=data)
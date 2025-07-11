from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Request
from app.core.schemas import BaseResponse
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserIndex, UserRead, UserReadMinimal
from fastapi_pagination import Params
from typing import Optional
from pydantic import BaseModel

class UserController:
    def __init__(self,  db: AsyncSession, is_admin: bool = False):
        self.db = db
        self.is_admin = is_admin
        self.repository = UserRepository(db)

    async def get(self, user_id: int):
        user = await self.repository.get(record_id=user_id, load_relations=["image", "city", "plans.start_city", "plans.image"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        public_plans = []
        for plan in user.plans:
            if not plan.is_private:
                public_plans.append(plan)
        user.plans = public_plans
        user_read = UserRead.model_validate(user, from_attributes=True)
        user.email = None if not self.is_admin else user.email
        user_read.no_of_plans = await self.repository.get_no_of_plans(user_id, include_private=self.is_admin)
        return BaseResponse(message="User fetched successfully", data=user_read)

    async def index(
        self,
        params: Params,
        search: Optional[str] = None,
        sort_by: Optional[str] = "id",
        order: Optional[str] = "asc",
    ):
        data = await self.repository.index(
            params=params,
            search_fields=["username"],
            search_query=search,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["image", "city"]
        )
        data = [UserIndex.model_validate(ts, from_attributes=True) for ts in data.items]
        for user in data:
            user.email = None if not self.is_admin else user.email
            user.no_of_plans = await self.repository.get_no_of_plans(user.id, include_private=self.is_admin)
            
        return BaseResponse(message="Users fetched successfully", data=data)
        
from typing import Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Params

from app.core.schemas import BaseResponse
from app.database.redis_cache import RedisCache
from app.modules.plans.cache import PlanCache
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schema import PlanBase, PlanCreate, PlanFiltersInternal, PlanIndex, PlanRead


class PlanController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.repository = PlanRepository(db)
        self.user_id = user_id

    async def create(self, plan: PlanCreate):
        plan_internal = PlanBase(user_id=self.user_id, **plan.model_dump())
        plan_db = await self.repository.create(plan_internal)
        plan_data = await self.repository.get_updated_plan(plan_db.id, user_id=self.user_id)
        return BaseResponse(message="Plan created successfully", data=plan_data)

    async def get(self, plan_id: int):
        plan = await self.repository.get_updated_plan(plan_id, user_id=self.user_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user.id != self.user_id and plan.is_private:
            raise HTTPException(status_code=403, detail="Plan is private")
        return BaseResponse(message="Plan fetched successfully", data=plan)
    
    async def delete(self, plan_id: int):
        plan = await self.repository.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your plans")
        delete = await self.repository.delete(plan_id)
        await self.graph_repository.delete(plan_id)
        return BaseResponse(message="Plan deleted successfully")
    
    async def update(self, plan_id: int, plan: PlanCreate):
        plan_internal = PlanBase(user_id=self.user_id, **plan.model_dump())
        past_data = await self.repository.get(plan_id, load_relations=["days.steps"])
        if past_data.start_city_id != plan.start_city_id and past_data.days and past_data.days[0].steps:
            raise HTTPException(status_code=403, detail="You can't change start city after adding steps")
        plan_db = await self.repository.update(plan_id, plan_internal)
        if not plan_db:
            raise HTTPException(status_code=404, detail="Plan not found")
        plan_data = await self.repository.get_updated_plan(plan_db.id, user_id=self.user_id)
        return BaseResponse(message="Plan updated successfully", data=plan_data)

    async def duplicate(self, plan_id: int):
        plan = await self.repository.duplicate_plan(plan_id, self.user_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        await self.graph_repository.create_from_sql_model(plan, self.user_id, self.db)
        plan_data = await self.repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Plan duplicated successfully", data=plan_data)

    async def index(
        self,
        params: Params,
        search: Optional[str] = None,
        sort_by: Optional[str] = "id",
        order: Optional[str] = "asc",
        filters: Optional[BaseModel] = None
    ):
        data = await self.repository.index(
            params=params,
            search_fields=["title"],
            search_query=search,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["start_city", "image", "user.image"],
            filters=PlanFiltersInternal(**filters.model_dump())
        )
        data=[PlanIndex.model_validate(ts, from_attributes=True) for ts in data.items]
        for d in data:
            d.is_saved = await self.repository.is_saved(self.user_id, d.id)
            d.self_rating = await self.repository.get_rating(self.user_id, d.id)
        return BaseResponse(message="Plans fetched successfully", data=data)
    
    async def rate(self, plan_id: int, rating: int):
        if not 1<=rating<=5:
            raise HTTPException(detail="Rating must be between 1 and 5", status_code=400)
        is_rated = await self.repository.rate_plan(self.user_id, plan_id, rating)
        if not is_rated:
            raise HTTPException(status_code=400, detail="You can't rate private plans")
        return BaseResponse(message="Plan rated successfully", data={"rating": rating})

    async def delete_rate(self, plan_id: int):
        rate_removed = await self.repository.remove_plan_rating(self.user_id, plan_id)
        if not rate_removed:
            raise HTTPException(status_code=404, detail="No rating found")
        return BaseResponse(message="Plan rating removed successfully")

    async def toggle_save(self, plan_id: int):
        saved = await self.repository.toggle_save_plan(self.user_id, plan_id)
        return BaseResponse(message="Plan saved successfully" if saved else "Plan unsaved successfully", data={"saved": saved})
    
    async def undo_changes(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days.steps.route_hops"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only undo changes to your plans")
        cached = await self.cache.pop(plan)
        if not cached:
            raise HTTPException(status_code=404, detail="No changes found")
        plan_data = await self.repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Plan duplicated successfully", data=plan_data)
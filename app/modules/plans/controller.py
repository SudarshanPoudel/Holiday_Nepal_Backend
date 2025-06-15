from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.repository import PlanDayStepRepositary
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayStepCreateInternal, PlanDayTimeFrameEnum
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schema import PlanCreate, PlanCreateInternal, PlanRead
from app.modules.plans.utils import PlanUtils


class PlanController():
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.repository = PlanRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.plan_day_step_repository = PlanDayStepRepositary(db)
        self.user_id = user_id
        self.utils = PlanUtils(db)

    async def create(self, plan: PlanCreate):
        plan_internal = PlanCreateInternal(user_id=self.user_id, end_municipality_id=plan.start_municipality_id, **plan.model_dump())
        plan_db = await self.repository.create(plan_internal)
        return BaseResponse(message="Plan created successfully", data={"id": plan_db.id})

    async def get(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days.steps.place", "days.steps.activities", "days.steps.municipality_start", "days.steps.municipality_end", "days.steps.image"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id and plan.is_private:
            raise HTTPException(status_code=403, detail="Plan is private")
        plan = PlanRead.model_validate(plan, from_attributes=True)
        return BaseResponse(message="Plan fetched successfully", data=plan)
    
    async def delete(self, plan_id: int):
        plan = await self.repository.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your plans")
        delete = await self.repository.delete(plan_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Plan not found")
        return BaseResponse(message="Plan deleted successfully")
    
    async def add_day(self, plan_id: int, title: str):
        plan = await self.repository.get(plan_id, load_relations=["days"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        plan_day = PlanDayCreate(
            plan_id=plan_id,
            title=title,
            day=len(plan.days) + 1
        )
        plan_day = await self.plan_day_repository.create(plan_day)
        return BaseResponse(message="Day added successfully", data={"id": plan_day.id})
    
    async def delete_day(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        await self.plan_day_repository.delete(plan.days[-1].id)
        return BaseResponse(message="Day deleted successfully")

    async def add_day_step(self, plan_id: int, step: PlanDayStepCreate):
        plan = await self.repository.get(plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        latest_day = plan.days[-1]
        
        
        time_frame = await self.utils.get_step_time_frame()
        duration = await self.utils.get_step_duration()
        image_id = await self.utils.get_step_image()
        current_municipality_id = await self.utils.get_curret_municipality_id()

        place_id = None
        municipality_start_id = None
        municipality_end_id = None
        title = None
        if step.category == PlanDayStepCategoryEnum.transport:
            municipality_start_id = current_municipality_id
            municipality_end_id = step.place_id
            title = "Go From A to B"
        else:
            place_id = step.place_id
            title = "Visit Place"
        step_internal = PlanDayStepCreateInternal(
            plan_day_id=latest_day.id,
            title=title,
            category=step.category,
            time_frame=time_frame,
            duration=duration,
            image_id=image_id,
            place_id=place_id,
            municipality_start_id=municipality_start_id,
            municipality_end_id=municipality_end_id
        )
        step = await self.plan_day_step_repository.create(step_internal)
        return BaseResponse(message="Day step added successfully", data={"id": step.id})
    
    async def delete_day_step(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        if len(plan.days[-1].steps) <= 0:
            raise HTTPException(status_code=403, detail="This day doesn't contain any steps.")
        await self.plan_day_step_repository.delete(plan.days[-1].steps[-1].id)
        return BaseResponse(message="Day step deleted successfully")
from typing import Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from app.modules.accomodation_services.repository import AccomodationServiceRepository
from app.modules.accomodation_services.schema import AccomodationServiceRead
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum

from app.core.schemas import BaseResponse
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate, PlanDayRead, PlanDayUpdate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.repository import PlanRepository

class PlanDayController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.repository = PlanDayRepository(db)
        self.accomodation_repository = AccomodationServiceRepository(db)
        self.plan_repository = PlanRepository(db)
        self.plan_day_step_service = PlanDayStepService(db, graph_db)

    async def update(self, plan_day_id: int, plan_day: PlanDayUpdate):
        plan_day_db = await self.repository.get(plan_day_id, load_relations=["plan"])
        if not plan_day_db:
            raise HTTPException(status_code=404, detail="Plan day not found")
        if plan_day_db.plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        await self.repository.update(plan_day_id, plan_day)
        plan_data = await self.plan_repository.get_updated_plan(plan_day_db.plan_id, user_id=self.user_id)
        return BaseResponse(message="Plan day updated successfully", data=plan_data)
    
    async def partial_update(self, plan_day_id: int, data: Dict):
        plan_day = await self.repository.get(plan_day_id, load_relations=["plan"])
        if not plan_day:
            raise HTTPException(status_code=404, detail="Plan day not found")
        if plan_day.plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        plan_day_db = await self.repository.update_from_dict(plan_day_id, data)
        if not plan_day_db:
            raise HTTPException(status_code=404, detail="Plan day not found")
        plan_data = await self.plan_repository.get_updated_plan(plan_day_db.plan_id, user_id=self.user_id)
        return BaseResponse(message="Plan day updated successfully", data=plan_data)
    

    async def add_day(self, plan_day: PlanDayCreate):
        plan = await self.plan_repository.get(plan_day.plan_id, load_relations=["days"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        day = len(plan.days)
        for day in plan.days[plan_day.index:]:
            await self.repository.update_from_dict(day.id, {"index": day.index+1})
        plan_day_db = await self.repository.create(plan_day)
        plan_data = await self.plan_repository.get_updated_plan(plan_day.plan_id, user_id=self.user_id)
        return BaseResponse(message="Day added successfully", data=plan_data)
    
    async def delete_day(self, plan_day_id: int):
        plan_day = await self.repository.get(plan_day_id, load_relations=["plan.days", "steps"])
        if not plan_day:
            raise HTTPException(status_code=404, detail="Plan day not found")
        plan = plan_day.plan
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        
        for step in reversed(plan_day.steps):
            is_deletable = await self.plan_day_step_service.delete(step.id, just_check=True)
            if not is_deletable:
                raise HTTPException(status_code=403, detail="You can't delete this day because it contains some steps that cannot be deleted.")
        
        for step in reversed(plan_day.steps):
            await self.plan_day_step_service.delete(step.id)
        await self.repository.delete(plan_day_id)

        for day in plan.days[plan_day.index:]:
            await self.repository.update_from_dict(day.id, {"index": day.index-1})

        await self.plan_repository.update_from_dict(plan.id, {"no_of_days": len(plan.days)-1})
        plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Day deleted successfully", data=plan_data)


    async def recommand_accomodation_services(self, plan_day_id: int):
        plan_day = await self.repository.get(plan_day_id, load_relations=["steps.place_activity.place"])
        if not plan_day:
            raise HTTPException(status_code=404, detail="Plan day not found")
        if not plan_day.steps:
            raise HTTPException(status_code=404, detail="No steps found for this plan day")
        
        last_city_id = None
        for step in reversed(plan_day.steps):
            if step.category == PlanDayStepCategoryEnum.transport:
                last_city_id = step.city_id
                break
            elif step.category == PlanDayStepCategoryEnum.visit:
                last_city_id = step.city_id
                break
            else:
                last_city_id = step.place_activity.place.city_id
                break

        if not last_city_id:
            raise HTTPException(status_code=404, detail="No city found for this plan day")
        
        services = await self.accomodation_repository.recommand(self.user_id, last_city_id, load_relations=["images", "city"])
        if not services:
            raise HTTPException(status_code=404, detail="No accomodation services found for this plan day")
        return BaseResponse(message="Accomodation services fetched successfully", data=[AccomodationServiceRead.model_validate(service, from_attributes=True) for service in services])

        
        
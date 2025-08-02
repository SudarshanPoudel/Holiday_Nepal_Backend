from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day_steps.repository import PlanDayStepRepository
from app.modules.transport_service.repository import TransportServiceRepository
from app.modules.transport_service.schema import TransportServiceRead, TransportServiceReadAll
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plans.repository import PlanRepository


class PlanDayStepController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.graph_db = graph_db
        self.user_id = user_id
        self.repository = PlanDayStepRepository(db)
        self.plan_repository = PlanRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.service = PlanDayStepService(db, graph_db)
        self.transport_service_repository = TransportServiceRepository(db)

    async def add_plan_day_step(self, step: PlanDayStepCreate):
        plan = await self.plan_repository.get(step.plan_id, load_relations=["days"])
        if not step.plan_day_id:
            if not plan.days:
                plan_day = await self.plan_day_repository.create(PlanDayCreate(plan_id=plan.id, index=0, title="Day 1 of " + plan.title))
                step.plan_day_id = plan_day.id
            else:
                step.plan_day_id = plan.days[-1].id
        plan_day = await self.plan_day_repository.get(step.plan_day_id, load_relations=["steps"])
        if not plan_day:
            raise HTTPException(status_code=404, detail=f"Plan Day not found {step.plan_day_id}")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        created_steps = await self.service.add(step)
        plan_data = await self.plan_repository.get_updated_plan(plan_day.plan.id, user_id=self.user_id)
        return BaseResponse(message="Step added successfully", data=plan_data)

    async def delete_day_step(self, plan_day_step_id: int):
        day_step = await self.repository.get(plan_day_step_id, load_relations=["plan_day.plan"])
        if not day_step:
            raise HTTPException(status_code=404, detail="Plan Day Step not found")
        plan = day_step.plan_day.plan
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your plans")
        await self.service.delete(plan_day_step_id)
        
        # Return updated plan data
        plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Day step deleted successfully", data=plan_data)
    
    async def reorder_day_step(self, plan_day_step_id: int, new_index: int):
        day_step = await self.repository.get(plan_day_step_id, load_relations=["plan_day.plan"])
        if not day_step:
            raise HTTPException(status_code=404, detail="Plan Day Step not found")
        plan = day_step.plan_day.plan
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your plans")
        await self.service.reorder(plan_day_step_id, new_index)
        plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Day step re-ordered successfully", data=plan_data)
    
    async def get_transport_services(self, plan_day_step_id: int):
        day_step = await self.repository.get(plan_day_step_id, load_relations=["plan_day.plan.days.steps"])
        if not day_step:
            raise HTTPException(status_code=404, detail="Plan Day Step not found")
        if day_step.category != PlanDayStepCategoryEnum.transport:
            raise HTTPException(status_code=400, detail="This step is not a transport step")
        last_city = None
        if day_step.index > 0:
            for day in day_step.plan_day.plan.days:
                if not last_city:
                    for steps in day.steps:
                        if steps.index == day_step.index - 1:
                            last_city = steps.city_id
                            break
                else:
                    break
        if not last_city:
            last_city = day_step.plan_day.plan.start_city_id

        services = await self.transport_service_repository.recommend_services(last_city, day_step.city_id)
        if not services:
            raise HTTPException(status_code=404, detail="No transport services found for this step")
        data = await self.transport_service_repository.get_multiple(services, load_relations=["images", "start_city", "end_city"])
        return BaseResponse(message="Transport services fetched successfully", data=[TransportServiceReadAll.model_validate(ts, from_attributes=True) for ts in data])
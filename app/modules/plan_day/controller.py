from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.accomodation_services.repository import AccomodationServiceRepository
from app.modules.accomodation_services.schema import AccomodationServiceRead
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.plan_day.graph import PlanDayGraphRepository, PlanDayNode, PlanDayPlanDayEdge, PlanPlanDayEdge
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate, PlanDayRead
from app.modules.plans.repository import PlanRepository

class PlanDayController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.graph_db = graph_db
        self.user_id = user_id
        self.repository = PlanDayRepository(db)
        self.graph_repository = PlanDayGraphRepository(graph_db)
        self.accomodation_repository = AccomodationServiceRepository(db)
        self.plan_repository = PlanRepository(db)

    async def update(self, plan_day_id: int, title: str):
        plan_day = await self.repository.get(plan_day_id, load_relations=["plan"])
        if not plan_day:
            raise HTTPException(status_code=404, detail="Plan day not found")
        if plan_day.plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        await self.repository.update_from_dict(plan_day_id, {"title": title})
        await self.graph_repository.update(PlanDayNode(id=plan_day_id, index=plan_day.index))
        plan_data = await self.plan_repository.get_updated_plan(plan_day.plan_id, user_id=self.user_id)
        return BaseResponse(message="Plan day updated successfully", data=plan_data)
    

    async def add_day(self, plan_id: int, title: str):
        plan = await self.plan_repository.get(plan_id, load_relations=["days"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        day=len(plan.days)
        plan_day = PlanDayCreate(
            plan_id=plan_id,
            title=title,
            index=day
        )
        plan_day = await self.repository.create(plan_day)
        await self.graph_repository.create(PlanDayNode(id=plan_day.id, index=plan_day.index))
        if day == 0:
            await self.graph_repository.add_edge(PlanPlanDayEdge(source_id=plan_id, target_id=plan_day.id))
        else:
            await self.graph_repository.add_edge(PlanDayPlanDayEdge(source_id=plan.days[-1].id, target_id=plan_day.id))
        await self.plan_repository.update_from_dict(plan_id, {"no_of_days": day+1})
        plan_data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
        return BaseResponse(message="Day added successfully", data=plan_data)
    
    async def delete_day(self, plan_id: int):
        plan = await self.plan_repository.get(plan_id, load_relations=["days"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        await self.repository.delete(plan.days[-1].id)
        await self.graph_repository.delete(plan.days[-1].id)
        await self.plan_repository.update_from_dict(plan_id, {"no_of_days": len(plan.days)-1})
        plan_data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
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
                last_city_id = step.end_city_id
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

        
        
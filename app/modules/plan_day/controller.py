from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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
        self.plan_repository = PlanRepository(db)

    async def update(self, plan_day_id: int, title: str):
        plan_day = await self.repository.get(plan_day_id, load_relations=["plan"])
        if not plan_day:
            raise HTTPException(status_code=404, detail="Plan day not found")
        if plan_day.plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        await self.repository.update_from_dict(plan_day_id, {"title": title})
        await self.graph_repository.update(PlanDayNode(id=plan_day_id, title=title))
        plan_data = self.plan_repository.get_updated_plan(plan_day.plan_id)
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
        await self.graph_repository.create(PlanDayNode(id=plan_day.id, index=plan_day.index, total_time=0, total_cost=0))
        if day == 0:
            await self.graph_repository.add_edge(PlanPlanDayEdge(source_id=plan_id, target_id=plan_day.id))
        else:
            await self.graph_repository.add_edge(PlanDayPlanDayEdge(source_id=plan.days[-1].id, target_id=plan_day.id))
        plan_data = await self.plan_repository.get_updated_plan(plan_id)
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
        plan_data = await self.plan_repository.get_updated_plan(plan_id)
        return BaseResponse(message="Day deleted successfully", data=plan_data)

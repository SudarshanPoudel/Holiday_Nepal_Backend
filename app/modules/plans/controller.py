from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.plans.graph import PlanGraphRepository, PlanNode
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schema import PlanCreate, PlanCreateInternal, PlanRead


class PlanController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.graph_db = graph_db
        self.repository = PlanRepository(db)
        self.graph_repository = PlanGraphRepository(graph_db)
        self.user_id = user_id

    async def create(self, plan: PlanCreate):
        plan_internal = PlanCreateInternal(user_id=self.user_id, **plan.model_dump())
        plan_db = await self.repository.create(plan_internal)
        await self.graph_repository.create(PlanNode(id=plan_db.id, user_id=self.user_id, no_of_people=plan.no_of_people, start_municipality_id=plan.start_municipality_id, end_municipality_id=plan.end_municipality_id)), 
        return BaseResponse(message="Plan created successfully", data={"id": plan_db.id})

    async def get(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days.steps.place", "days.steps.activities", "days.steps.municipality_start", "days.steps.municipality_end", "days.steps.image", "days.steps.route_hops", "user.image"])
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
        await self.graph_repository.delete(plan_id)
        return BaseResponse(message="Plan deleted successfully")
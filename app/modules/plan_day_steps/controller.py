from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.plan_day_steps.schema import PlanDayStepCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.repository import PlanRepository


class PlanDayStepController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.graph_db = graph_db
        self.user_id = user_id
        self.plan_repository = PlanRepository(db)
        self.service = PlanDayStepService(db, graph_db)

    async def add_plan_day_step(self, step: PlanDayStepCreate):
        """Add a new step to the plan, automatically adding transport if needed"""
        plan = await self.plan_repository.get(step.plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        created_steps = await self.service.add_step_to_plan(plan, step, insert_in_graph=True)
        plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Step added successfully", data=plan_data)

    async def delete_day_step(self, plan_id: int):
        """Delete the last step from the plan"""
        # Validate plan access and get plan object
        plan = await self._validate_plan_access(plan_id)
        
        # Use service to delete step
        await self.service.delete_last_step_from_plan(plan, insert_in_graph=True)
        
        # Return updated plan data
        plan_data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
        return BaseResponse(message="Day step deleted successfully", data=plan_data)
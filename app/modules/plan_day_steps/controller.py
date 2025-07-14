from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.transport_service.graph import TransportServiceGraphRepository
from app.modules.transport_service.repository import TransportServiceRepository
from app.modules.transport_service.schema import TransportServiceRead, TransportServiceReadAll
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
        self.transport_service_repository = TransportServiceRepository(db)
        self.transport_service_graph_repository = TransportServiceGraphRepository(graph_db)

    async def add_plan_day_step(self, step: PlanDayStepCreate):
        plan = await self.plan_repository.get(step.plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        created_steps = await self.service.add_step_to_plan(plan, step, insert_in_graph=True)
        plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
        return BaseResponse(message="Step added successfully", data=plan_data)

    async def delete_day_step(self, plan_id: int):
        plan = await self.plan_repository.get(plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your plans")
        # Use service to delete step
        await self.service.delete_last_step_from_plan(plan, insert_in_graph=True)
        
        # Return updated plan data
        plan_data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
        return BaseResponse(message="Day step deleted successfully", data=plan_data)
    
    async def get_transport_services(self, plan_day_step_id: int):
        services = await self.transport_service_graph_repository.recommend_services_matching_plan_hops(plan_day_step_id)
        if not services:
            raise HTTPException(status_code=404, detail="No transport services found for this step")
        data = await self.transport_service_repository.get_multiple(services, load_relations=["images", "start_city", "end_city"])
        return BaseResponse(message="Transport services fetched successfully", data=[TransportServiceReadAll.model_validate(ts, from_attributes=True) for ts in data])
from typing import Optional
from fastapi import  WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.redis_cache import RedisCache
from app.modules.ai.agent.llm import LLM
from app.modules.ai.agent.planner import TripPlannerAgent
from app.modules.ai.agent.schema import AgentAlreadyDoneTaskBase, AgentImprovedPromptBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.modules.cities.repository import CityRepository
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.cache import PlanCache
from app.modules.plans.repository import PlanRepository
from neo4j import AsyncSession as Neo4jSession
from rapidfuzz import process, fuzz
import traceback
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate
from app.modules.plans.schema import  PlanBase


class AIController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, redis: RedisCache, user_id: int):
        self.user_id = user_id
        self.plan_repository = PlanRepository(db)
        self.city_repository = CityRepository(db)
        self.place_repository = PlaceRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.plan_day_step_service = PlanDayStepService(db, graph_db)
        self.agent = TripPlannerAgent(db)
        self.plan_cache = PlanCache(db, redis)

    async def generate_plan_websocket(self, prompt: str, websocket: WebSocket):
        await websocket.send_json({
            "type": "prompt",
            "response": prompt
        })
        debug_mode = True
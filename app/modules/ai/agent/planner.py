from pprint import pprint
from typing import List, Dict, Any
from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.ai.agent.llm import LLM
from app.modules.ai.agent.schema import AgentAlreadyDoneTaskBase, AgentImprovedPromptBase, AgentOverallPlanBase, AgentOverallPlanDayBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.modules.ai.agent.prompts import get_prompt, OVERALL_PLAN_GENERATION_PROMPT, PROMPT_IMPROVEMENT_PROMPT, SINGLE_DAY_EXPANDING_PROMPT
from app.modules.cities.models import City
from app.modules.cities.repository import CityRepository
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository

class TripPlannerAgent:
    def __init__(self, db: AsyncSession):  
        self.db = db
        self.city_repository = CityRepository(db)
        self.place_repository = PlaceRepository(db)

    async def generate_plan(prompt: str, user_id: int):
        pass


    async def generate_plan_json(prompt: str, user_id: int):
        pass
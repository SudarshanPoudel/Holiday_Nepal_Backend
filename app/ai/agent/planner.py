from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.agent.llm import LLM
from app.ai.agent.schema import AgentImprovedPromptBase, AgentOverallPlanBase, AgentOverallPlanDayBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.ai.agent.prompts import get_prompt, OVERALL_PLAN_GENERATION_PROMPT, PROMPT_IMPROVEMENT_PROMPT, SINGLE_DAY_EXPANDING_PROMPT
from app.core.schemas import BaseResponse
from app.modules.cities.models import City
from app.modules.cities.repository import CityRepository
from app.modules.cities.schema import CityRead
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


class TripPlannerAgent:
    def __init__(self, db: AsyncSession):  
        self.db = db
        self.city_repository = CityRepository(db)
        self.place_repository = PlaceRepository(db)

    async def generate_plan(self, prompt: str) -> AgentPlanBase:
        improved_prompt = await self.improve_prompt(prompt)
        overall_plan = await self.generate_overall_plan(improved_prompt.refined_prompt)
        expanded_plan = await self.expand_overall_plan(overall_plan)
        return expanded_plan

    # Step 1
    async def improve_prompt(self, prompt: str) -> AgentImprovedPromptBase:
        user_pref = {"lives_in": "Bharatpur"}  # TODO: track and use real user pref
        prompt = get_prompt(PROMPT_IMPROVEMENT_PROMPT, user_prompt=prompt, user_pref=user_pref, start_end_city=user_pref["lives_in"])
        resp = LLM.get_structured_response(prompt, AgentImprovedPromptBase)
        return resp

    # Step 2
    async def generate_overall_plan(self, prompt: str) -> AgentOverallPlanBase:
        similar_cities = await self.city_repository.vector_search(prompt, limit=10)
        cities = [s.name for s in similar_cities]
        prompt = get_prompt(OVERALL_PLAN_GENERATION_PROMPT, prompt=prompt, cities=cities)
        resp = LLM.get_structured_response(prompt, AgentOverallPlanBase)
        return resp

    # Step 3 - New method to expand a single day
    async def expand_single_day(
        self, 
        day: AgentOverallPlanDayBase, 
        day_index: int, 
        already_done_tasks: Dict[str, List[str]], 
        upcoming_days_description: List[Dict[int, str]]
    ) -> AgentPlanDayBase:
        available_cities = [await self.db.scalar(
                select(City).where(City.name == city)
            ) for city in day.cities]
        city_ids = [c.id for c in available_cities if c is not None]

        available_places = await self.place_repository.vector_search(
            day.description, 
            limit=10, 
            extra_conditions=[Place.city_id.in_(city_ids)], 
            load_relations=["place_activities.activity"]
        )

        place_names_and_activities = []
        for place in available_places:
            place_names_and_activities.append({
                "place": place.name, 
                "duration (hr)": place.average_visit_duration,
                "cost (npr)": place.average_visit_cost,
                "activities": [{
                    "name": a.activity.name,
                    "duration (hr)": a.average_duration,
                    "cost (npr)": a.average_cost,
                } for a in place.place_activities] if place.place_activities else ["NOT AVAILABLE"]
            })
        
        prompt = get_prompt(
            SINGLE_DAY_EXPANDING_PROMPT, 
            already_done_tasks=already_done_tasks, 
            day_description=day.description, 
            day_index=day_index, 
            upcoming_days=upcoming_days_description, 
            places=place_names_and_activities
        )
        steps = LLM.get_structured_response(prompt, AgentPlanDayStepBase)
        
        # Create the expanded day
        expanded_day = AgentPlanDayBase(
            title=day.title,
            steps=steps
        )
        return expanded_day

    async def expand_overall_plan(self, overall_plan: AgentOverallPlanBase) -> AgentPlanBase:
        already_done_tasks = {}
        expanded_days = []
        
        for i, day in enumerate(overall_plan.days):
            day_index = i + 1
            upcoming_days_description = [
                {j: d.description} for j, d in enumerate(overall_plan.days[i + 1:])
            ]

            expanded_day = await self.expand_single_day(
                day=day,
                day_index=day_index,
                already_done_tasks=already_done_tasks,
                upcoming_days_description=upcoming_days_description
            )
            
            expanded_days.append(expanded_day)

        return AgentPlanBase(
            title=overall_plan.title,
            description=overall_plan.description,
            days=expanded_days
        )
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

    async def generate_plan(self, prompt: str) -> AgentPlanBase:
        improved_prompt = await self.improve_prompt(prompt)
        overall_plan = await self.generate_overall_plan(improved_prompt.refined_prompt)
        expanded_plan = await self.expand_overall_plan(overall_plan)
        return expanded_plan

    # Step 1
    async def improve_prompt(self, chat_history: str) -> AgentImprovedPromptBase:
        user_pref = {"lives_in": "Bharatpur"}  # TODO: track and use real user pref
        prompt = get_prompt(PROMPT_IMPROVEMENT_PROMPT, chat_history=chat_history, user_pref=user_pref, start_city=user_pref["lives_in"])
        resp = await LLM.get_structured_response(prompt, AgentImprovedPromptBase)
        return resp

    # Step 2
    async def generate_overall_plan(self, prompt: str, no_of_days: int = 5) -> AgentOverallPlanBase:
        similar_cities = await self.city_repository.vector_search(prompt, limit=no_of_days*2)
        cities = [s.name for s in similar_cities]
        prompt = get_prompt(OVERALL_PLAN_GENERATION_PROMPT, prompt=prompt, no_of_days=no_of_days, cities=cities)
        resp = await LLM.get_structured_response(prompt, AgentOverallPlanBase)
        return resp

    # Step 3 - New method to expand a single day
    async def expand_single_day(
        self, 
        day: AgentOverallPlanDayBase, 
        already_done_tasks: List[AgentAlreadyDoneTaskBase], 
        upcoming_days: List[AgentOverallPlanDayBase]
    ) -> AgentPlanDayBase:
        already_done_task_md = ""
        already_included_places = []
        current_city = already_done_tasks[0].name
        for task in already_done_tasks:
            if task.category == "visit":
                already_done_task_md += f"- Visited {task.name}\n"
                already_included_places.append(task.id)
            elif task.category == "activity":
                already_done_task_md += f"- Did {task.name}\n"
            elif task.category == "transport":
                already_done_task_md += f"- Traveled from {current_city} to {task.name}\n"
                current_city = task.name
            else:
                continue

        upcoming_days_md = "\n-".join([
            f"day_{j}: {d.description}" for j, d in enumerate(upcoming_days)
        ])


        available_cities = [
            await self.db.scalar(
                select(City).where(func.lower(City.name) == city.lower())
            )
            for city in day.cities
        ]
        city_ids = [c.id for c in available_cities if c is not None]

        available_places = await self.place_repository.vector_search(
            day.description, 
            limit=5, 
            extra_conditions = [
                and_(
                    Place.city_id.in_(city_ids),
                    not_(Place.id.in_(already_included_places))
                )
            ],
            load_relations=["place_activities.activity"]
        )

        place_md_list = ""

        for place in available_places:
            place_md_list += f"### {place.name} (**{place.average_visit_duration} hr) \n"
            if place.place_activities:
                place_md_list += f"- Activities:\n"
                for pa in place.place_activities:
                    place_md_list += f"  - {pa.activity.name} (**{pa.average_duration} hr**)\n"
            else:
                place_md_list += f"- Activities: _NOT AVAILABLE_\n"
            place_md_list += "\n"

        prompt = get_prompt(
            SINGLE_DAY_EXPANDING_PROMPT, 
            already_done_tasks=already_done_task_md, 
            day_description=day.description, 
            upcoming_days=upcoming_days_md, 
            places=place_md_list
        )

        steps = await LLM.get_structured_response(prompt, AgentPlanDayStepBase)
        
        # Create the expanded day
        expanded_day = AgentPlanDayBase(
            title=day.title,
            steps=steps
        )
        return expanded_day
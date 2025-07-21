from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.ai.agent.llm import LLM
from app.ai.agent.prompts import PLAN_EDIT_EXTRACTION_PROMPT, PLAN_EDIT_PROMPT, get_prompt
from app.ai.agent.schema import AgentEditDataSearchBase, AgentEditResponseBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.modules.places.repository import PlaceRepository
from app.modules.plans.controller import PlanController
from app.modules.plans.repository import PlanRepository


class TripEditorAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_repository = PlanRepository(db)
        self.place_repository = PlaceRepository(db)

    async def edit_plan(self, plan: AgentPlanBase, prompt: str):
        plan_with_edit_index = self._convert_plan_to_edit_index(plan)
        extract_prompt = get_prompt(PLAN_EDIT_EXTRACTION_PROMPT, plan=plan_with_edit_index, prompt=prompt)
        resp: AgentEditDataSearchBase = LLM.get_structured_response(extract_prompt, AgentEditDataSearchBase)

        if resp.query and resp.top_n:
            available_places = await self.place_repository.vector_search(resp.query, limit=resp.top_n, load_relations=["place_activities.activity"])
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
        
        edit_prompt = get_prompt(PLAN_EDIT_PROMPT, plan=plan_with_edit_index, places=place_names_and_activities, prompt=prompt)
        resp = LLM.get_structured_response(edit_prompt, AgentEditResponseBase)
        plan = self._rebuild_plan_from_edit_index(plan_with_edit_index, resp.plan)
        return plan


    def _convert_plan_to_edit_index(self, plan: AgentPlanBase) -> dict:
        result = {
            "title": plan.title,
            "description": plan.description
        }

        for day_index, day in enumerate(plan.days, start=1):
            day_key = f"day_{day_index}"
            result[day_key] = {
                f"{day_key}_title": day.title
            }
            for step_index, step in enumerate(day.steps, start=1):
                step_key = f"{day_key}_step_{step_index}"
                result[day_key][step_key] = step.dict()

        return result
    
    def _rebuild_plan_from_edit_index(self, original: dict, edited: dict) -> AgentPlanBase:
        def resolve_value(key: str):
            return edited.get(key, "unchanged") if edited.get(key) != "unchanged" else original.get(key)

        plan_title = resolve_value("title")
        plan_description = resolve_value("description")

        days = []
        day_keys = [k for k in edited.keys() if k.startswith("day_") and isinstance(edited[k], dict)]

        for day_key in sorted(day_keys, key=lambda k: int(k.split("_")[1])):
            day_dict = edited[day_key]
            original_day_dict = original.get(day_key, {})

            # Get the day title
            day_title_key = f"{day_key}_title"
            day_title = day_dict.get(day_title_key, "unchanged")
            if day_title == "unchanged":
                day_title = original_day_dict.get(day_title_key)

            # Get steps
            steps = []
            for step_key in sorted(day_dict.keys()):
                if step_key == day_title_key:
                    continue
                step_data = day_dict[step_key]
                if step_data == "unchanged":
                    step_data = original_day_dict.get(step_key)
                steps.append(AgentPlanDayStepBase(**step_data))

            days.append(AgentPlanDayBase(title=day_title, steps=steps))

        return AgentPlanBase(title=plan_title, description=plan_description, days=days)

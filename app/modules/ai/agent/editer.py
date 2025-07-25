from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.places.models import Place
from app.modules.plan_day_steps.service import PlanDayStepService
from neo4j import AsyncSession as Neo4jSession

from app.modules.ai.agent.llm import LLM
from app.modules.ai.agent.prompts import DAY_ADDITION_PROMPT, PLAN_EDIT_CLASSIFICATION_PROMPT, PLAN_SIMPLE_EDIT_PROMPT, PLAN_COMPLEX_EDIT_PROMPT, get_prompt
from app.modules.ai.agent.schema import AgentEditPromptRefine, AgentEditType, AgentImprovedPromptBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase, AgentSimpleEditRequestBase
from app.modules.places.repository import PlaceRepository
from app.modules.plans.repository import PlanRepository


class TripEditorAgent:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.plan_repository = PlanRepository(db)
        self.place_repository = PlaceRepository(db)
        self.plan_day_step_service = PlanDayStepService(db, graph_db)

    async def structure_edit_request(self, plan: AgentPlanBase, history: str) -> AgentEditPromptRefine:
        plan_with_edit_index = self._convert_plan_to_edit_index(plan)
        edit_type_prompt = get_prompt(PLAN_EDIT_CLASSIFICATION_PROMPT, plan=plan_with_edit_index, chat_history=history)
        type_resp = await LLM.get_structured_response(edit_type_prompt, AgentEditType)
        if type_resp.type == "unrelated":
            return AgentEditPromptRefine(type="none", response=type_resp.response, edit=None)
        if type_resp.type == "simple":
            extract_prompt = get_prompt(PLAN_SIMPLE_EDIT_PROMPT, plan=plan_with_edit_index, prompt=type_resp.response)
            edit_resp = await LLM.get_structured_response(extract_prompt, AgentSimpleEditRequestBase)
        else:
            extract_prompt = get_prompt(PLAN_COMPLEX_EDIT_PROMPT, plan=plan_with_edit_index, prompt=type_resp.response)
            edit_resp = await LLM.get_structured_response(extract_prompt, AgentImprovedPromptBase)
        return AgentEditPromptRefine(type=type_resp.type, response=type_resp.response, edit=edit_resp)
    
    async def structure_steps_to_add(self, day: AgentPlanDayBase, step_desc: str) -> List[AgentPlanDayStepBase]:
        existing_places = [step.place for step in day.steps]
        resp = await self.place_repository.vector_search(
            step_desc, limit=4,
            extra_conditions=[Place.name.notin_(existing_places)],
            load_relations=["place_activities.activity"]
        )

        place_md_list = ""

        for place in resp:
            place_md_list += f"### {place.name} (**{place.average_visit_duration} hr) \n"
            if place.place_activities:
                place_md_list += f"- Activities:\n"
                for pa in place.place_activities:
                    place_md_list += f"  - {pa.activity.name} (**{pa.average_duration} hr**)\n"
            else:
                place_md_list += f"- Activities: _NOT AVAILABLE_\n"
            place_md_list += "\n"

        
        prompt = get_prompt(DAY_ADDITION_PROMPT, places=place_md_list, step_desc=step_desc, steps=[step.model_dump() for step in day.steps])
        resp = await LLM.get_structured_response(prompt, AgentPlanDayStepBase)
        return resp


    def _convert_plan_to_edit_index(self, plan: AgentPlanBase) -> dict:
        result = {
            "title": plan.title,
            "description": plan.description
        }
        
        step_index = 0
        for day_index, day in enumerate(plan.days):
            day_key = f"day_{day_index}"
            result[day_key] = {
                f"{day_key}_title": day.title
            }
            for step in day.steps:
                step_key = f"step_{step_index}"
                result[day_key][step_key] = step.model_dump()
                step_index += 1

        return result
    
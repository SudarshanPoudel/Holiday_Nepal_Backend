import json
import random
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.agent.planner import TripPlannerAgent
from app.ai.agent.schema import AgentPlanBase
from app.core.websocket_utils import safe_json_dumps
from app.modules.activities.repository import ActivityRepository
from app.modules.cities.repository import CityRepository
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.controller import PlanDayController
from app.modules.plan_day_steps.controller import PlanDayStepController
from app.modules.plans.controller import PlanController
from neo4j import AsyncSession as Neo4jSession
from typing import List
from rapidfuzz import process, fuzz
import traceback

from app.core.schemas import BaseResponse
from app.modules.plan_day.graph import PlanDayGraphRepository, PlanDayNode
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.graph import PlanCityEdge, PlanGraphRepository, PlanNode
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schema import PlanBase, PlanCreate


class AIController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.plan_controller = PlanController(db, graph_db, user_id)
        self.plan_day_controller = PlanDayController(db, graph_db, user_id)
        self.plan_day_step_controller = PlanDayStepController(db, graph_db, user_id)
        self.city_repository = CityRepository(db)
        self.activity_repository = ActivityRepository(db)
        self.place_activity_repository = PlaceActivityRepository(db)
        self.place_repository = PlaceRepository(db)
        self.agent = TripPlannerAgent(db)

    async def generate_plan_websocket(self, prompt: str, websocket: WebSocket):
        try:
            await websocket.send_text(safe_json_dumps({
                "type": "progress",
                "message": "Improving prompt...",
                "step": "prompt_improvement"
            }))
            
            improved_prompt = await self.agent.improve_prompt(prompt)
            
            await websocket.send_text(safe_json_dumps({
                "type": "progress",
                "message": "Finding start city...",
                "step": "city_lookup"
            }))
            
            start_city = await self.city_repository.get_similar(improved_prompt.start_city, limit=1)
            
            await websocket.send_text(safe_json_dumps({
                "type": "progress",
                "message": "Generating overall plan...",
                "step": "plan_generation"
            }))
            
            overall_plan = await self.agent.generate_overall_plan(improved_prompt.refined_prompt)
            
            plan_create = PlanCreate(
                title=overall_plan.title,
                description=overall_plan.description,
                start_city_id=start_city[0].id,
                no_of_people=improved_prompt.no_of_people
            )
            
            await websocket.send_text(safe_json_dumps({
                "type": "progress",
                "message": "Creating plan in database...",
                "step": "plan_creation"
            }))
            
            # CREATE PLAN
            plan_created_response = await self.plan_controller.create(plan_create)
            
            # Send the complete plan_created_response
            await websocket.send_text(safe_json_dumps({
                "type": "plan_created",
                "response": plan_created_response.data.model_dump()
            }))
            
            plan_id = plan_created_response.data.id
            already_done_tasks = {}
            expanded_days = []
            
            total_days = len(overall_plan.days)
            
            for i, day in enumerate(overall_plan.days):
                await websocket.send_text(safe_json_dumps({
                    "type": "progress",
                    "message": f"Processing day {i + 1} of {total_days}...",
                    "step": "day_processing",
                    "current_day": i + 1,
                    "total_days": total_days
                }))
                
                city_ids = []
                for city in day.cities:
                    c = await self.city_repository.get_similar(city, limit=1)
                    city_ids.append(c[0].id)
                    
                day_index = i + 1
                upcoming_days_description = [
                    {j: d.description} for j, d in enumerate(overall_plan.days[i + 1:])
                ]
                
                expanded_day = await self.agent.expand_single_day(
                    day=day,
                    day_index=day_index,
                    already_done_tasks=already_done_tasks,
                    upcoming_days_description=upcoming_days_description
                )
                
                expanded_days.append(expanded_day)
                
                # CREATE DAY
                day_created_response = await self.plan_day_controller.add_day(plan_id, expanded_day.title)
                
                # Send the complete day_created_response
                await websocket.send_text(safe_json_dumps({
                    "type": "day_created",
                    "response": day_created_response.data.model_dump()
                }))
                
                already_done_tasks[f"day_{day_index}"] = []
                total_steps = len(expanded_day.steps)
                
                for step_idx, step in enumerate(expanded_day.steps):
                    await websocket.send_text(safe_json_dumps({
                        "type": "progress",
                        "message": f"Adding step {step_idx + 1} of {total_steps} to day {day_index}...",
                        "step": "step_processing",
                        "current_step": step_idx + 1,
                        "total_steps": total_steps,
                        "current_day": day_index
                    }))
                    
                    place_id = None
                    place_activity_id = None
                    end_city_id = None
                    
                    if step.category == "visit":
                        category = PlanDayStepCategoryEnum.visit
                        p = await self.place_repository.get_similar(step.place, limit=1, extra_conditions=[Place.city_id.in_(city_ids)])
                        place_id = p[0].id
                        already_done_tasks[f"day_{day_index}"].append(f"Visit - {step.place}")
                        
                    elif step.category == "activity":
                        category = PlanDayStepCategoryEnum.activity
                        place = p[0]
                        activities = place.place_activities
                        choices = {
                            a: a.activity.name for a in activities if a.activity and a.activity.name
                        }
                        matches = process.extract(
                            step.place_activity[1],
                            choices,
                            scorer=fuzz.ratio,
                            limit=1
                        )
                        best_match_obj = matches[0][0]
                        place_activity_id = best_match_obj.id
                        matched_activity_name = best_match_obj.activity.name
                        already_done_tasks[f"day_{day_index}"].append(
                            f"Activity - {matched_activity_name} at {step.place_activity[0]}"
                        )
                        
                    elif step.category == "travel":
                        category = PlanDayStepCategoryEnum.transport
                        ec = await self.city_repository.get_similar(step.end_city, limit=1)
                        end_city_id = ec[0].id
                        already_done_tasks[f"day_{day_index}"].append(f"Travel to {step.end_city}")
                    
                    # CREATE STEP
                    step_added_response = await self.plan_day_step_controller.add_plan_day_step(
                        PlanDayStepCreate(
                            plan_id=plan_id,
                            category=category,
                            place_id=place_id,
                            end_city_id=end_city_id,
                            place_activity_id=place_activity_id
                        )
                    )
                    
                    # Send the complete step_added_response
                    await websocket.send_text(safe_json_dumps({
                        "type": "step_created",
                        "response": step_added_response.dict() if hasattr(step_added_response, 'dict') else step_added_response.__dict__
                    }))
            
            # Send final result
            final_result = AgentPlanBase(
                title=overall_plan.title,
                description=overall_plan.description,
                days=expanded_days
            )
            
            await websocket.send_text(safe_json_dumps({
                "type": "completed",
                "data": {
                    "title": final_result.title,
                    "description": final_result.description,
                    "days": [day.dict() if hasattr(day, 'dict') else day for day in final_result.days]
                }
            }))
            
        except Exception as e:
            traceback.print_exc()
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": str(e)
            }))
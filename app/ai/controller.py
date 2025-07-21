from fastapi import HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.agent.editer import TripEditorAgent
from app.ai.agent.planner import TripPlannerAgent
from app.ai.agent.schema import AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.core.schemas import BaseResponse
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
from rapidfuzz import process, fuzz
import traceback
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate
from app.modules.plans.schema import  PlanCreate, PlanRead


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
        self.edit_agent = TripEditorAgent(db)

    async def edit_plan(self, plan_id: int, prompt: str):
        plan_resp = await self.plan_controller.get(plan_id)
        plan: PlanRead = plan_resp.data
        agent_plan_days = []
        for days in plan.days:
            day_steps = []
            for day_step in days.steps:
                place_name = None
                category = day_step.category.value
                if category == "activity":
                    place = await self.place_repository.get(day_step.place_activity.place_id)
                    place_name = place.name if place else None
                if category == "transport":
                    category = "travel"
                day_steps.append(AgentPlanDayStepBase(
                    category=category,
                    place=day_step.place.name if day_step.place else None,
                    place_activity=(place_name, day_step.place_activity.activity.name) if day_step.place_activity else None,
                    end_city=day_step.city_end.name if day_step.city_end else None
                ))

            agent_plan_days.append(AgentPlanDayBase(
                title=days.title,
                steps=day_steps
            ))

        agent_plan = AgentPlanBase(
            title=plan.title,
            description=plan.description,
            days=agent_plan_days
        )

        edited_plan = await self.edit_agent.edit_plan(agent_plan, prompt)
        await self.plan_controller.update(plan_id, PlanCreate(
            title=edited_plan.title,
            description=edited_plan.description,
            start_city_id=plan.start_city.id,
            no_of_people=plan.no_of_people,
            image_id=plan.image.id,
            is_private=plan.is_private
        ))
        
        while True:
            try:
                await self.plan_day_controller.delete_day(plan_id)
            except HTTPException as e:
                break
        
        final_data = None
        for day in edited_plan.days:
            resp = await self.plan_day_controller.add_day(plan_id, day.title)
            for step in day.steps:
                place_id = None
                place_activity_id = None
                end_city_id = None
                
                if step.category == "visit":
                    category = PlanDayStepCategoryEnum.visit
                    p = await self.place_repository.get_similar(step.place, limit=1)
                    place_id = p[0].id
                    
                elif step.category == "activity":
                    category = PlanDayStepCategoryEnum.activity
                    p = await self.place_repository.get_similar(step.place, limit=1, load_relations=["place_activities.activity"])
                    activities = p[0].place_activities
                    choices = [a.activity.name for a in activities]

                    matches = process.extract(
                        step.place_activity[1],
                        choices,
                        scorer=fuzz.ratio,
                        limit=1
                    )
                    best_match_choice = matches[0][0]
                    best_match_obj = [a for a in activities if a.activity.name == best_match_choice][0]
                    place_activity_id = best_match_obj.id
                    matched_activity_name = best_match_obj.activity.name
                    
                else:
                    category = PlanDayStepCategoryEnum.transport
                    ec = await self.city_repository.get_similar(step.end_city, limit=1)
                    end_city_id = ec[0].id
                
                # CREATE STEP
                final_data = await self.plan_day_step_controller.add_plan_day_step(
                    PlanDayStepCreate(
                        plan_id=plan_id,
                        category=category,
                        place_id=place_id,
                        end_city_id=end_city_id,
                        place_activity_id=place_activity_id
                    )
                )
        return BaseResponse(message="Plan edited successfully", data=final_data.data)
                



    async def generate_plan_websocket(self, prompt: str, websocket: WebSocket):
        try:
            improved_prompt = await self.agent.improve_prompt(prompt)
            
            start_city = await self.city_repository.get_similar(improved_prompt.start_city, limit=1)
            
            overall_plan = await self.agent.generate_overall_plan(improved_prompt.refined_prompt)
            
            plan_create = PlanCreate(
                title=overall_plan.title,
                description=overall_plan.description,
                start_city_id=start_city[0].id,
                no_of_people=improved_prompt.no_of_people
            )
            
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
            
            
            for i, day in enumerate(overall_plan.days):
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
                    "type": "day_added",
                    "response": day_created_response.data.model_dump()
                }))
                
                todays_task = []
                
                for step in expanded_day.steps:
                    place_id = None
                    place_activity_id = None
                    end_city_id = None
                    
                    if step.category == "visit":
                        category = PlanDayStepCategoryEnum.visit
                        p = await self.place_repository.get_similar(step.place, limit=1, extra_conditions=[Place.city_id.in_(city_ids)])
                        if not p:
                            p = await self.place_repository.get_similar(step.place, limit=1)
                        place_id = p[0].id
                        place_id = p[0].id
                        todays_task.append(f"Visited - {step.place}")
                        
                    elif step.category == "activity":
                        category = PlanDayStepCategoryEnum.activity
                        p = await self.place_repository.get_similar(step.place, limit=1, extra_conditions=[Place.city_id.in_(city_ids)], load_relations=["place_activities.activity"])
                        if not p:
                            p = await self.place_repository.get_similar(step.place, limit=1, load_relations=["place_activities.activity"])
                        activities = p[0].place_activities
                        choices = [a.activity.name for a in activities]

                        matches = process.extract(
                            step.place_activity[1],
                            choices,
                            scorer=fuzz.ratio,
                            limit=1
                        )
                        best_match_choice = matches[0][0]
                        best_match_obj = [a for a in activities if a.activity.name == best_match_choice][0]
                        place_activity_id = best_match_obj.id
                        matched_activity_name = best_match_obj.activity.name
                        todays_task.append(f"Did {matched_activity_name} at {step.place}")
                        
                    else:
                        category = PlanDayStepCategoryEnum.transport
                        ec = await self.city_repository.get_similar(step.end_city, limit=1)
                        end_city_id = ec[0].id
                        todays_task.append(f"Travelled to {step.end_city}")
                    
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
                        "response": step_added_response.data.model_dump()
                    }))

                    
                already_done_tasks[f"day_{day_index}"] = todays_task
            
            # Send final result
            final_result = AgentPlanBase(
                title=overall_plan.title,
                description=overall_plan.description,
                days=expanded_days
            )
            

            await websocket.send_text(safe_json_dumps({
                "type": "completed"
            }))
            
        except Exception as e:
            traceback.print_exc()
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": str(e)
            }))
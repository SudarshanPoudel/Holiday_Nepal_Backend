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

    async def generate_plan_websocket(self, prompt: str, websocket: WebSocket, improved_prompt : Optional[AgentImprovedPromptBase]=None, plan_id: Optional[int] = None):
        await websocket.send_json({
            "type": "prompt",
            "response": prompt
        })
        debug_mode = True
        events_md = "- Removed existing plan steps to generate from scratch according to asked changes"
        try:
            if not improved_prompt:
                improved_prompt = await self.agent.improve_prompt(chat_history=f"user: {prompt}")
                events_md = "- Generating brand new plan according to user request"
            if debug_mode:
                await websocket.send_json({
                    "type": "improved_prompt",
                    "response": jsonable_encoder(improved_prompt)
                })
            
            start_city = await self.city_repository.get_similar(improved_prompt.start_city, limit=1)
            
            overall_plan = await self.agent.generate_overall_plan(improved_prompt.refined_prompt)

            if debug_mode:
                await websocket.send_json({
                    "type": "overall_plan",
                    "response": jsonable_encoder(overall_plan)
                })
            
            if not plan_id:
                plan_create = PlanBase(
                    user_id=self.user_id,
                    title=overall_plan.title,
                    description=overall_plan.description,
                    start_city_id=start_city[0].id,
                    no_of_people=improved_prompt.no_of_people
                )
                
                # CREATE PLAN
                plan_db = await self.plan_repository.create(plan_create)
                plan_id = plan_db.id
            
            plan = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)

            # Send the complete plan_created_response
            await websocket.send_json({
                "type": "plan_created",
                "response": jsonable_encoder(plan)
            })
            
            already_done_tasks = [AgentAlreadyDoneTaskBase(category="start_from", name=start_city[0].name, id=start_city[0].id)]
            already_visited_places = set()
            for i, day in enumerate(overall_plan.days):
                city_ids = []
                for city in day.cities:
                    c = await self.city_repository.get_similar(city, limit=1)
                    city_ids.append(c[0].id)
                                    
                
                expanded_day = await self.agent.expand_single_day(
                    day=day,
                    already_done_tasks=already_done_tasks,
                    upcoming_days=overall_plan.days[i+1:]
                )
                
                if debug_mode:
                    await websocket.send_json({
                        "type": "day_expanded",
                        "response": jsonable_encoder(expanded_day)
                    })
                                
                # CREATE DAY
                day_db = await self.plan_day_repository.create(PlanDayCreate(
                    plan_id=plan_id,
                    index=i,
                    title=expanded_day.title
                ))
                day_id = day_db.id
                plan = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
                
                # Send the complete day_created_response
                await websocket.send_json({
                    "type": "day_created",
                    "response": jsonable_encoder(plan)
                })
                
                for step in expanded_day.steps:
                    place_id = None
                    place_activity_id = None
                    city_id = None
                    
                    if step.category == "visit":
                        p = await self.place_repository.get_similar(step.place, limit=1, extra_conditions=[Place.city_id.in_(city_ids)], min_score=50)
                        if not p:
                            p = await self.place_repository.get_similar(step.place, limit=1, min_score=50)
                        if not p:
                            continue
                        place_id = p[0].id
                        already_visited_places.add(p[0].id)
                        already_done_tasks.append(AgentAlreadyDoneTaskBase(category="visit", name=p[0].name, id=place_id))
                        
                    elif step.category == "activity":
                        p = await self.place_repository.get_similar(step.place_activity[0], limit=1, extra_conditions=[Place.city_id.in_(city_ids)], load_relations=["place_activities.activity"], min_score=50)
                        if not p:
                            p = await self.place_repository.get_similar(step.place_activity[0], limit=1, load_relations=["place_activities.activity"], min_score=50)
                        if not p:
                            continue
                        activities = p[0].place_activities
                        choices = [a.activity.name for a in activities]
                        if not choices:
                            if p[0].id not in already_visited_places:
                                already_done_tasks.append(AgentAlreadyDoneTaskBase(category="visit", name=p[0].name, id=p[0].id))
                                step.category = "visit"
                                place_id = p[0].id
                            continue

                        matches = process.extract(
                            step.place_activity[1],
                            choices,
                            scorer=fuzz.ratio,
                            limit=1
                        )
                        best_match_choice = matches[0][0]
                        best_match_obj = [a for a in activities if a.activity.name == best_match_choice][0]
                        place_activity_id = best_match_obj.id
                        already_done_tasks.append(AgentAlreadyDoneTaskBase(category="activity", name=f"{best_match_choice} at {p[0].name}", id=place_activity_id))
                        
                    else:
                        ec = await self.city_repository.get_similar(step.city, limit=1, min_score=50)
                        if not ec:
                            continue
                        city_id = ec[0].id
                        skip_transport = False
                        for t in reversed(already_done_tasks):
                            if t.category in ["transport", "start_from"]:
                                skip_transport = (t.id == city_id)
                                break
                        if skip_transport:
                            continue
                        already_done_tasks.append(AgentAlreadyDoneTaskBase(category="transport", name=ec[0].name, id=city_id))    
                        
                    
                    # CREATE STEP
                    try:
                        await self.plan_day_step_service.add(
                            PlanDayStepCreate(
                                plan_id=plan_id,
                                plan_day_id=day_id,
                                category=PlanDayStepCategoryEnum(step.category),
                                place_id=place_id,
                                city_id=city_id,
                                place_activity_id=place_activity_id
                            )
                        )
                        plan = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
                        await websocket.send_json({
                            "type": "step_added",
                            "response": jsonable_encoder(plan)
                        })
                    except Exception as e:
                        traceback.print_exc()
                        raise
                        # continue           

            for task in already_done_tasks:
                if task.category == "visit":
                    events_md += f"- Added step to visit {task.name}\n"
                elif task.category == "activity":
                    events_md += f"-Added step to do {task.name}\n"
                elif task.category == "transport":
                    events_md += f"- Added step to travel to {task.name} city\n"
                else:
                    continue
            
            final_resp = await LLM.get_events_response(events_md, prompt)

            await websocket.send_json({
                "type": "completed",
                "response": final_resp
            })
            
        except Exception as e:
            raise e
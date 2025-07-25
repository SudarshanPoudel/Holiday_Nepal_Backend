from pprint import pprint
from typing import Literal, Optional
from fastapi import HTTPException, WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.redis_cache import RedisCache
from app.modules.ai.agent.editer import TripEditorAgent
from app.modules.ai.agent.llm import LLM
from app.modules.ai.agent.planner import TripPlannerAgent
from app.modules.ai.agent.schema import AgentAlreadyDoneTaskBase, AgentImprovedPromptBase, AgentPlanBase, AgentPlanDayBase, AgentPlanDayStepBase
from app.modules.ai.cache import AICache
from app.modules.ai.schema import AIChat
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
        self.edit_agent = TripEditorAgent(db, graph_db)
        self.ai_cache = AICache(redis)




    async def edit_plan(self, plan_id: int, prompt: str, websocket: WebSocket):
        await self.ai_cache.push(self.user_id, plan_id, AIChat(sender="user", message=prompt))
        events_md = "# Plan Edit Request"
        try:
            plan = await self.plan_repository.get(plan_id, load_relations=["start_city", "days.steps.city", "days.steps.place_activity.place", "days.steps.place_activity.activity", "days.steps.place"])
            if plan.user_id != self.user_id:
                raise HTTPException(status_code=403, detail="You can only edit your plans")
            
            await self.plan_cache.push(plan_id)
            
            agent_plan_days = []
            for days in plan.days:
                day_steps = []
                for day_step in days.steps:
                    place_name = None
                    category = day_step.category.value
                    if category == "activity":
                        place = await self.place_repository.get(day_step.place_activity.place_id)
                        place_name = place.name if place else None
                    day_steps.append(AgentPlanDayStepBase(
                        category=category,
                        place=day_step.place.name if day_step.place else None,
                        place_activity=(place_name, day_step.place_activity.activity.name) if day_step.place_activity else None,
                        city=day_step.city.name if day_step.city else None
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

            history = await self.ai_cache.get_history(self.user_id, plan_id)
            edit_structured_base = await self.edit_agent.structure_edit_request(agent_plan, history)  
            edit_structured = edit_structured_base.edit
            await websocket.send_json({
                "type": "edit_structured",
                "response": jsonable_encoder(edit_structured.model_dump())
            })

            if edit_structured_base.type == "unrelated":
                await self.ai_cache.push(self.user_id, plan_id, AIChat(sender="ai", message=edit_structured_base.response))
                await websocket.send_json({
                    "type": "edit_structured",
                    "response": edit_structured_base.response
                })
                return

            if edit_structured_base.type == "simple":
                index_reduce = 0
                for removing_index in edit_structured.to_remove: 
                    id, title = await self.get_id_from_index(plan, removing_index)
                    try:
                        await self.plan_day_step_service.delete(id)
                        events_md += f"\n# Removed step: `{title}`"

                        data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
                        index_reduce += 1
                    except Exception as e:
                        events_md += f"\n# Failed to remove step: {title}"
                
                for from_index, to_index in edit_structured.to_reorder:
                    try:
                        id, title = await self.get_id_from_index(plan, from_index - index_reduce)
                        try:
                            await self.plan_day_step_service.reorder(id, to_index)
                            events_md += f"\n# Reordered step: `{title}` as asked"
                        except Exception as e:
                            events_md += f"\n# Failed to reorder step: `{title}`"
                        data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
                        await websocket.send_json({
                            "type": "step_reordered",
                            "response": jsonable_encoder(data)
                        })
                    except Exception as e:
                        events_md += f"\n# Failed to reorder step: `{title}`"

                for addition in edit_structured.to_add:
                    day = agent_plan.days[addition.day_index]
                    structured_add = await self.edit_agent.structure_steps_to_add(day=day, step_desc=addition.steps_description)
                    pprint([s.model_dump() for s in structured_add])
                    for step in structured_add:
                        place_id = None
                        place_activity_id = None
                        city_id = None
                        
                        if step.category == "visit":
                            p = await self.place_repository.get_similar(step.place, limit=1, min_score=50)
                            if not p:
                                continue
                            place_id = p[0].id
                            
                        elif step.category == "activity":
                            p = await self.place_repository.get_similar(step.place, limit=1, load_relations=["place_activities.activity"], min_score=50)
                            if not p:
                                continue
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
                            
                        else:
                            ec = await self.city_repository.get_similar(step.city, limit=1, min_score=50)
                            if not ec:
                                continue
                            city_id = ec[0].id
                        
                        # CREATE STEP
                        try:
                            step_added_response = await self.plan_day_step_service.add(
                                PlanDayStepCreate(
                                    plan_day_id=plan.days[addition.day_index].id,
                                    category=PlanDayStepCategoryEnum(step.category),
                                    place_id=place_id,
                                    city_id=city_id,
                                    place_activity_id=place_activity_id
                                )
                            )
                            title = step_added_response.title
                            events_md += f"\n# Added step: `{title}`"

                            data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
                            websocket.send_json({
                                "type": "step_added",
                                "response": jsonable_encoder(data)
                            })
                        except Exception as e:
                            events_md += f"\n# Failed to add step: `{title}`"

                history = await self.ai_cache.get_history(self.user_id, plan_id)
                final_response = await LLM.get_events_response(events_md, history)
                await self.ai_cache.push(self.user_id, plan_id, AIChat(sender="ai", message=final_response))
                await websocket.send_json({
                    "type": "success",
                    "response": final_response
                })

            else:
                for day in reversed(plan.days):
                    await self.plan_day_repository.delete(day.id)
                await websocket.send_json({
                    "type": "days_removed",
                    "response": jsonable_encoder(day)
                })
                if not edit_structured.no_of_people:
                    edit_structured.no_of_people = plan.no_of_people
                if not edit_structured.start_city:
                    edit_structured.start_city = plan.start_city.name
                await self.generate_plan_websocket(prompt=edit_structured.refined_prompt, websocket=websocket, improved_prompt=edit_structured, plan_id=plan_id)

        except Exception as e:
            plan = await self.plan_repository.get(plan_id, load_relations=["days.steps.route_hops"])
            await self.plan_cache.pop(plan)
            history = await self.ai_cache.get_history(self.user_id, plan_id)
            final_response = await LLM.get_events_response(f"# Some error occured : \n{str(e)[:200]}.... So plan has been restored", history)
            await self.ai_cache.push(self.user_id, plan_id, AIChat(sender="ai", message=final_response))
            await websocket.send_json({
                "type": "error",
                "response": final_response
            })

            traceback.print_exc()







    async def generate_plan_websocket(self, prompt: str, websocket: WebSocket, improved_prompt : Optional[AgentImprovedPromptBase]=None, plan_id: Optional[int] = None):
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
                await self.ai_cache.push(self.user_id, plan_id,AIChat(sender="user", message=prompt))
            
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
            
            history = await self.ai_cache.get_history(self.user_id, plan_id)
            final_resp = await LLM.get_events_response(events_md, history)

            await self.ai_cache.push(self.user_id, plan_id, AIChat(sender="ai", message=final_resp))

            await websocket.send_json({
                "type": "completed",
                "response": final_resp
            })
            
        except Exception as e:
            raise e
    











    async def get_id_from_index(self, plan, index, look_into:Literal["steps", "days"] = "steps"):
        for day in plan.days:
            if look_into == "steps":
                for step in day.steps:
                    if step.index == index:
                        return step.id, step.title
                    continue                    
            if day.index == index:
                return day.id, step.title
from typing import List
from fastapi import  WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.redis_cache import RedisCache
from app.modules.ai.agent.llm import LLM
from app.modules.ai.agent.planner import TripPlannerAgent
from app.modules.cities.repository import CityRepository
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.cache import PlanCache
from app.modules.plans.models import Plan
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
        try:
            await websocket.send_json({"type": "prompt", "response": prompt})
            plan: Plan | None = None
            last_itinerary_index = -1
            day_no_and_id_map: dict[int, int] = {}
            prev_day_id: int | None = None
            prev_city_id: int | None = None
            day_step_index_map: dict[int, int] = {}  # track last added step index per day

            async for resp in self.agent.generate_overall_plan(prompt, self.user_id):
                # --- First response (plan metadata only) ---
                if plan is None and resp.title and resp.description:
                    plan = await self.plan_repository.create(
                        PlanBase(title=resp.title, description=resp.description, user_id=self.user_id)
                    )
                    await websocket.send_json({
                        "type": "plan_created",
                        "response": await self._get_plan_json(plan.id)
                    })
                    continue

                # --- Process newly added itineraries ---
                if plan and len(resp.itinerary) - 1 > last_itinerary_index:
                    new_items = resp.itinerary[last_itinerary_index + 1:]
                    last_itinerary_index = len(resp.itinerary) - 1

                    for itinerary in new_items:
                        # Fallback no_of_days calculation
                        no_of_days = 5
                        if itinerary.departure:
                            arrival_day = itinerary.arrival.day if itinerary.arrival else 0
                            no_of_days = max(1, itinerary.departure.day - arrival_day)

                        city_db = await self.city_repository.get_similar(itinerary.city, limit=1)

                        if not prev_city_id:
                            await self.plan_repository.update_from_dict(plan.id, {"start_city_id": city_db[0].id})
                        

                        if not itinerary.travel_around:
                            if prev_city_id and prev_city_id != city_db[0].id:
                                await self.plan_day_step_service.add(
                                    PlanDayStepCreate(
                                        plan_id=plan.id,
                                        day_id=day_no_and_id_map.get(itinerary.arrival.day),
                                        category=PlanDayStepCategoryEnum.transport,
                                        city_id=city_db[0].id
                                    )
                                )
                            prev_city_id = city_db[0].id
                            continue
                    
                        prev_city_id = city_db[0].id
                        # --- Stream single city plan (days + steps) ---
                        async for city_days in self.agent.generate_single_city_plan(itinerary, no_of_days):
                            for day in city_days:
                                day_id = day_no_and_id_map.get(day.day)

                                # --- Create new day if not exists ---
                                if not day_id:
                                    day_db = await self.plan_day_repository.create(
                                        PlanDayCreate(plan_id=plan.id, title=day.title)
                                    )
                                    day_id = day_db.id
                                    day_no_and_id_map[day.day] = day_id
                                    day_step_index_map[day.day] = -1  # init step tracker

                                    if prev_day_id:
                                        await self.plan_day_repository.update_from_dict(
                                            prev_day_id, {"next_plan_day_id": day_id}
                                        )
                                    prev_day_id = day_id

                                # --- Add only new steps ---
                                last_index = day_step_index_map.get(day.day, -1)
                                new_steps = day.steps[last_index + 1:]
                                if not new_steps:
                                    continue

                                for step in new_steps:
                                    place_db_list = await self.place_repository.get_similar(
                                        step.place, limit=1, load_relations=["place_activities.activity"],extra_conditions=[
                                            Place.city_id == prev_city_id
                                        ]
                                    )
                                    place_db = place_db_list[0]
                                    activity_db = None
                                    if step.category == "activity":
                                        choices = {act.activity.name: act for act in place_db.place_activities if act.activity.name}
                                        if choices:
                                            match_string, _, _ = process.extractOne(
                                                step.activity,
                                                choices.keys()
                                            )
                                            activity_db = choices[match_string]


                                    await self.plan_day_step_service.add(PlanDayStepCreate(
                                        plan_id=plan.id,
                                        plan_day_id=day_id,
                                        category=PlanDayStepCategoryEnum(step.category),
                                        place_id=place_db.id,
                                        place_activity_id=activity_db.id if activity_db else None,
                                    ))
                                    # --- Push updated plan snapshot after new steps ---
                                    await websocket.send_json({
                                        "type": "step_added",
                                        "response": await self._get_plan_json(plan.id)
                                    })
                                    
                                day_step_index_map[day.day] = len(day.steps) - 1

            await websocket.send_json({"type": "completed"})
        except Exception as e:
            print(traceback.format_exc())
            await websocket.send_json({"type": "error", "response": str(e)})

    async def _get_plan_json(self, plan_id):
        plan = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
        return plan.model_dump()    
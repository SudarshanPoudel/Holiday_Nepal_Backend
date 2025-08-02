from sqlalchemy.ext.asyncio import AsyncSession
from app.database.redis_cache import RedisCache
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.repository import PlanDayStepRepository
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreateInternal
from app.modules.plan_route_hops.repository import PlanRouteHopsRepository
from app.modules.plan_route_hops.schema import PlanRouteHopCreate
from app.modules.plans.repository import PlanRepository


class PlanCache:
    def __init__(self, db: AsyncSession ,redis_cache: RedisCache):
        self.cache = redis_cache
        self.db = db
        self.repository = PlanRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.plan_day_step_repository = PlanDayStepRepository(db)
        self.plan_route_hop_repository = PlanRouteHopsRepository(db)

    async def push(self, plan_id: int):
        plan = await self.repository.get(plan_id, load_relations=["days.steps.route_hops"])
        
        days_list = []
        for day in plan.days:
            step_list = []
            for step in day.steps:
                hop_list = []
                for route in step.route_hops:
                    hop_list.append({
                        "route_id": route.id,
                        "index": route.index,
                        "destination_city_id": route.destination_city_id,
                    })
                
                step_list.append({
                    "id": step.id,
                    "index": step.index,
                    "title": step.title,
                    "category": step.category.value,
                    "duration": step.duration,
                    "cost": step.cost,
                    "place_id": step.place_id,
                    "place_activity_id": step.place_activity_id,
                    "city_id": step.city_id,
                    "image_id": step.image_id,
                    "route_hops": hop_list,
                })
            
            days_list.append({
                "id": day.id,
                "index": day.index,
                "title": day.title,
                "steps": step_list,
            })

        plan_dict = {
            "title": plan.title,
            "description": plan.description,
            "no_of_days": plan.no_of_days,
            "no_of_people": plan.no_of_people,
            "estimated_cost": plan.estimated_cost,
            "is_private": plan.is_private,
            "image_id": plan.image_id,
            "start_city_id": plan.start_city_id,
            "days": days_list,
        }
        
        await self.cache.set(f"plan:{plan_id}", plan_dict)


    async def pop(self, plan):
        plan_id = plan.id
        cached = await self.cache.get(f"plan:{plan_id}")
        if not cached:
            return
        
        base_fields = {k: v for k, v in cached.items() if k != "days"}
        await self.repository.update_from_dict(plan_id, base_fields)

        current_day_map = {day.id: day for day in plan.days}
        cached_day_ids = {d["id"] for d in cached["days"] if d.get("id")}

        for day in plan.days:
            if day.id not in cached_day_ids:
                await self.plan_day_repository.delete(day.id)

        for cached_day in cached["days"]:
            day_id = cached_day.get("id")
            if day_id in current_day_map:
                await self.plan_day_repository.update_from_dict(day_id, {
                    "index": cached_day["index"],
                    "title": cached_day["title"],
                })
            else:
                day_db = await self.plan_day_repository.create(PlanDayCreate(
                    plan_id=plan_id,
                    index=cached_day["index"],
                    title=cached_day["title"],
                ))
                day_id = day_db.id

            day_obj = current_day_map.get(day_id)
            current_step_map = {
                step.id: step for step in (day_obj.steps if day_obj else [])
            }

            cached_step_ids = {s["id"] for s in cached_day["steps"] if s.get("id")}
            for step in current_step_map.values():
                if step.id not in cached_step_ids:
                    await self.plan_day_step_repository.delete(step.id)

            for cached_step in cached_day["steps"]:
                step_id = cached_step.get("id")
                if step_id in current_step_map:
                    await self.plan_day_step_repository.update_from_dict(step_id, {
                        "index": cached_step["index"],
                        "title": cached_step["title"],
                        "category": PlanDayStepCategoryEnum(cached_step["category"]),
                        "duration": cached_step["duration"],
                        "cost": cached_step["cost"],
                        "place_id": cached_step["place_id"],
                        "place_activity_id": cached_step["place_activity_id"],
                        "city_id": cached_step["city_id"],
                        "image_id": cached_step["image_id"],
                    })
                else:
                    step_db = await self.plan_day_step_repository.create(PlanDayStepCreateInternal(
                        plan_day_id=day_id,
                        index=cached_step["index"],
                        title=cached_step["title"],
                        category=PlanDayStepCategoryEnum(cached_step["category"]),
                        duration=cached_step["duration"],
                        cost=cached_step["cost"],
                        place_id=cached_step["place_id"],
                        place_activity_id=cached_step["place_activity_id"],
                        city_id=cached_step["city_id"],
                        image_id=cached_step["image_id"],
                    ))
                    step_id = step_db.id

                step_obj = current_step_map.get(step_id)
                current_hop_map = {
                    hop.id: hop for hop in (step_obj.route_hops if step_obj else [])
                }

                cached_hop_ids = {h["id"] for h in cached_step["route_hops"] if h.get("id")}
                for hop in current_hop_map.values():
                    if hop.id not in cached_hop_ids:
                        await self.plan_route_hop_repository.delete(hop.id)

                for cached_hop in cached_step["route_hops"]:
                    hop_id = cached_hop.get("id")
                    if hop_id in current_hop_map:
                        await self.plan_route_hop_repository.update_from_dict(hop_id, {
                            "index": cached_hop["index"],
                            "destination_city_id": cached_hop["destination_city_id"]
                        })
                    else:
                        await self.plan_route_hop_repository.create(PlanRouteHopCreate(
                            plan_day_step_id=step_id,
                            index=cached_hop["index"],
                            route_id=cached_hop["route_id"],
                            destination_city_id=cached_hop["destination_city_id"]
                        ))



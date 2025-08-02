from fastapi import HTTPException
from httpx import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.plans.models import Plan
from app.modules.plans.repository import PlanRepository
from neo4j import AsyncSession as Neo4jSession
from typing import List, Optional, Tuple

from app.modules.cities.graph import CityGraphRepository
from app.modules.cities.repository import CityRepository
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day_steps.repository import PlanDayStepRepository
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayStepCreateInternal
from app.modules.plan_route_hops.repository import PlanRouteHopsRepository
from app.modules.plan_route_hops.schema import PlanRouteHopCreate
from app.modules.plan_day_steps.utils import get_step_details, get_step_title
from app.modules.transport_route.graph import TransportRouteEdge
from app.modules.transport_route.repository import TransportRouteRepository


class PlanDayStepService:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = PlanDayStepRepository(db)
        self.place_repository = PlaceRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.city_repository = CityRepository(db)
        self.plan_route_hop_repository = PlanRouteHopsRepository(db)
        self.plan_repository = PlanRepository(db)
        self.transport_route_repository = TransportRouteRepository(db)
        self.place_activity_repository = PlaceActivityRepository(db)
        if graph_db:
            self.city_graph_repository = CityGraphRepository(graph_db)

    async def add(self, step: PlanDayStepCreate, add_single_transport: bool = False):
        step = await self._refactor_step(step)
        step_day = await self.plan_day_repository.get(step.plan_day_id, load_relations=["plan.days.steps"])
        if not step_day:
            raise HTTPException(status_code=404, detail="Plan Day not found")
        
        plan = step_day.plan
        days = plan.days
        current_day_index = step_day.index

        min_index = 0
        for i in range(current_day_index - 1, -1, -1):  # go backwards to find last step
            prev_day = days[i]
            if prev_day.steps:
                last_step = prev_day.steps[-1] 
                min_index = last_step.index + 1
                break
        max_index = min_index + len(step_day.steps)
        
        if step.index is not None:
            if not (min_index <= step.index <= max_index):
                raise HTTPException(
                    status_code=400,
                    detail=f"Step index must be between {min_index} and {max_index} for this day."
                )
        else:
            step.index = max_index  
        all_steps = []
        for day in plan.days:
            for s in day.steps:
                all_steps.append(s)

        if step.index is None:
            step.index = len(all_steps)

        prev_step: PlanDayStep = all_steps[step.index-1] if step.index > 0 else None
        next_step: PlanDayStep = all_steps[step.index] if step.index < len(all_steps)    else None
        prev_step_city_id = prev_step.city_id if prev_step else plan.start_city_id
        next_step_city_id = next_step.city_id if next_step else None

        steps_to_add = []
        steps_to_remove = []

        # if it's a transport step
        if step.category == PlanDayStepCategoryEnum.transport:
            if prev_step_city_id == step.city_id or (next_step_city_id and step.city_id == next_step_city_id): 
                return
            
            if next_step_city_id and next_step_city_id != step.city_id and next_step.category == PlanDayStepCategoryEnum.transport:
                steps_to_remove.append(next_step)

            
            steps_to_add.append(step)
            
            if next_step_city_id:
                steps_to_add.append(PlanDayStepCreate(
                    plan_id = step.plan_id,
                    plan_day_id=next_step.plan_day_id if (next_step and next_step.category == PlanDayStepCategoryEnum.transport) else step.plan_day_id,
                    category=PlanDayStepCategoryEnum.transport,
                    index=step.index + 1,
                    city_id=next_step_city_id
                ))

        elif step.city_id == prev_step_city_id:
            steps_to_add.append(step)
        
        else:
            if next_step and next_step.category == PlanDayStepCategoryEnum.transport:
                steps_to_remove.append(next_step)
            steps_to_add.append(PlanDayStepCreate(
                plan_id = step.plan_id,
                plan_day_id=step.plan_day_id,
                category=PlanDayStepCategoryEnum.transport,
                index=step.index,
                city_id=step.city_id
            ))
            steps_to_add.append(PlanDayStepCreate(
                **step.model_dump(exclude="index"),
                index=step.index + 1
            ))

            if next_step_city_id and next_step_city_id != step.city_id:
                steps_to_add.append(PlanDayStepCreate(
                    plan_id = step.plan_id,
                    plan_day_id=next_step.plan_day_id if (next_step and next_step.category == PlanDayStepCategoryEnum.transport) else step.plan_day_id,
                    category=PlanDayStepCategoryEnum.transport,
                    index=step.index + 2,
                    city_id=next_step_city_id
                ))

        # Update index
        for st in all_steps[step.index:]:
            await self.repository.update_from_dict(st.id, {"index": st.index + len(steps_to_add)})

        prev_id = prev_step_city_id
        for s in steps_to_add:
            step_details = await get_step_details(self.db, self.graph_db, prev_id, s)
            step_title = await get_step_title(self.db, s, prev_id)
            step_internal = PlanDayStepCreateInternal(
                plan_day_id=s.plan_day_id,
                title=step_title,
                category=s.category,
                duration=step_details["duration"],
                cost=step_details["cost"],
                image_id=step_details["image"].id if step_details["image"] else None,
                place_id=s.place_id,
                city_id=s.city_id,
                index=s.index,
                place_activity_id=s.place_activity_id
            )
            step_db = await self.repository.create(step_internal)
            if s.category == PlanDayStepCategoryEnum.transport:
                await self._create_transport_route_hops(step_db, prev_id, s.city_id)

            prev_id = s.city_id

        for s in steps_to_remove:
            for st in all_steps[s.index-len(steps_to_add):]:
                await self.repository.update_from_dict(st.id, {"index": st.index - 1})
            await self.repository.delete(s.id)

        return step_db
    

    async def delete(self, step_id: int, force=False):
        step = await self.repository.get(step_id, load_relations=["plan_day.plan.days.steps"])
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        plan_day = step.plan_day
        plan = plan_day.plan

        
        can_delete = await PlanDayStepService._can_delete_step(plan, step) if not force else True
        if not can_delete:
            raise HTTPException(status_code=400, detail="Can't delete this step.")
    
        all_steps = [s for day in plan.days for s in day.steps]
        if step.category != PlanDayStepCategoryEnum.transport:
            for st in all_steps[step.index:]:
                await self.repository.update_from_dict(st.id, {"index": st.index - 1})
            await self.repository.delete(step_id)
            return True

        # Transport Step Deletion Logic
        index = step.index
        prev_step = all_steps[index - 1] if index > 0 else None
        next_step = all_steps[index + 1] if index + 1 < len(all_steps) else None

        if not next_step:
            await self.repository.delete(step_id)
            return True

        if next_step.category == PlanDayStepCategoryEnum.transport:
            prev_step_city = prev_step.city_id if prev_step else plan.start_city_id
            if prev_step_city == next_step.city_id:
                for st in all_steps[step.index:]:
                    await self.repository.update_from_dict(st.id, {"index": st.index - 1})
                await self.repository.delete(next_step.id)
                
            else:
                next_step_create = PlanDayStepCreate(
                    plan_id=plan.id,
                    plan_day_id=step.plan_day_id,
                    category=PlanDayStepCategoryEnum.transport,
                    city_id=next_step.city_id
                )
                details = await get_step_details(self.db, self.graph_db, prev_step_city, next_step_create)
                title = await get_step_title(self.db, next_step_create, prev_step_city)
                await self.repository.update_from_dict(next_step.id, {
                    "duration": details["duration"],
                    "cost": details["cost"],
                    "image_id": details["image"].id if details["image"] else None,
                    "title": title
                })

        else:
            raise HTTPException(status_code=400, detail="Can't delete transport step that leads to visit or activity")

        for st in all_steps[step.index:]:
            await self.repository.update_from_dict(st.id, {"index": st.index - 1})
        await self.repository.delete(step_id)

        return True

    async def reorder(self, step_id: int, new_index: int):
        step = await self.repository.get(step_id)
        day = await self.plan_day_repository.get(step.plan_day_id)
        step_create = PlanDayStepCreate(
            plan_id = day.plan_id,
            plan_day_id=step.plan_day_id,
            category=step.category,
            place_id=step.place_id,
            place_activity_id=step.place_activity_id,
            city_id=step.city_id,
            index=new_index
        )
        try:
            await self.delete(step_id)
            await self.add(step_create)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed to reorder step")
        
    async def handle_change_start_city(self, plan_id, start_city_id):
        print(f"Plan {plan_id} start city changed to {start_city_id}")
        plan = await self.plan_repository.get(plan_id, load_relations=["days.steps"])
        first_step = None
        all_steps = []
        for day in plan.days:
            for step in day.steps:
                all_steps.append(step)
                if not first_step:
                    first_step = step
        
        if not first_step:
            return True
        print(f"First step city {first_step.city_id}")
        index_change = 0
        if first_step.city_id != start_city_id and first_step.category != PlanDayStepCategoryEnum.transport:
            s = PlanDayStepCreate(
                plan_id=plan_id,
                plan_day_id=first_step.plan_day_id,
                category=PlanDayStepCategoryEnum.transport,
                city_id=first_step.city_id,
                index=0  
            )
            index_change += 1
            step_details = await get_step_details(self.db, self.graph_db, start_city_id, s)
            step_title = await get_step_title(self.db, s, start_city_id)
            step_internal = PlanDayStepCreateInternal(
                plan_day_id=s.plan_day_id,
                title=step_title,
                category=s.category,
                duration=step_details["duration"],
                cost=step_details["cost"],
                image_id=step_details["image"].id if step_details["image"] else None,
                place_id=s.place_id,
                city_id=s.city_id,
                index=s.index,
                place_activity_id=s.place_activity_id
            )
            step_db = await self.repository.create(step_internal)
            if s.category == PlanDayStepCategoryEnum.transport:
                await self._create_transport_route_hops(step_db, start_city_id, s.city_id)

        elif first_step.city_id == start_city_id:
            index_change -= 1
            print(f"Removing first step {first_step.id}")
            await self.repository.delete(first_step.id)
            all_steps.pop(0)

        elif first_step.category == PlanDayStepCategoryEnum.transport:
            step_db = await self.repository.get(first_step.id, load_relations=["route_hops"])
            for hops in step_db.route_hops:
                await self.plan_route_hop_repository.delete(hops.id)
            step_details = await get_step_details(self.db, self.graph_db, start_city_id, first_step)
            title = await get_step_title(self.db, first_step, start_city_id)
            await self.repository.update_from_dict(step_db.id, {
                "duration": step_details["duration"],
                "cost": step_details["cost"],
                "image_id": step_details["image"].id if step_details["image"] else None,
                "title": title
            })
            await self._create_transport_route_hops(step_db, start_city_id, first_step.city_id)
        
        for step in all_steps:
            await self.repository.update_from_dict(step.id, {"index": step.index + index_change})
            


    async def _refactor_step(self, step: PlanDayStepCreate):
        """Clean up step data based on category"""
        if step.category == PlanDayStepCategoryEnum.transport:
            step.place_id = None
            step.place_activity_id = None
            if not step.city_id:
                raise HTTPException(status_code=400, detail="Transport steps require city_id")
        elif step.category == PlanDayStepCategoryEnum.visit:
            step.place_activity_id = None
            if not step.place_id:
                raise HTTPException(status_code=400, detail="Visit steps require place_id")
            place = await self.place_repository.get(step.place_id)
            step.city_id = place.city_id
        elif step.category == PlanDayStepCategoryEnum.activity:
            if not step.place_activity_id:
                raise HTTPException(status_code=400, detail="Activity steps require place_activity_id")
            activity = await self.place_activity_repository.get(step.place_activity_id, load_relations=['place'])
            step.city_id = activity.place.city_id
            step.place_id = activity.place_id
        else:
            raise HTTPException(status_code=400, detail="Invalid step category")
        
        return step
    
    async def _create_transport_route_hops(self, step_db, prev_city_id: int, city_id: int):
        """Create route hops for a transport step"""
        route_to_follow = await self.city_graph_repository.shortest_path(
            prev_city_id, 
            city_id, 
            edge_type=TransportRouteEdge, 
            weight_property="distance"
        )
        if not route_to_follow:
            raise HTTPException(status_code=404, detail="No route found")
        
        for i, (route_id, destination_city_id) in enumerate(route_to_follow):
            await self._create_route_hop(step_db.id, i, route_id, destination_city_id)

    async def _create_route_hop(self, step_id: int, index: int, route_id: int, destination_city_id: int):
        """Create a single route hop"""
        return await self.plan_route_hop_repository.create(
            PlanRouteHopCreate(
                plan_day_step_id=step_id,
                index=index,
                route_id=route_id,
                destination_city_id=destination_city_id
            )
        )
    
    
    @staticmethod
    async def _can_delete_step(plan: Plan, step: PlanDayStep):
        all_steps = [s for day in plan.days for s in day.steps]
        if step.category != PlanDayStepCategoryEnum.transport:
            return True
        index = step.index
        prev_index = None
        next_step = None
        for st in all_steps:
            if st.index > index:
                next_step = st
                break

        if not next_step:
            return True
        
        if next_step.category == PlanDayStepCategoryEnum.transport:
            return True
        else:
            return False  # transport → non-transport: can't delete
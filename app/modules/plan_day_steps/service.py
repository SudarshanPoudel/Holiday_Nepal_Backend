from typing import Optional
from fastapi import HTTPException
from httpx import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.plans.models import Plan
from app.modules.plans.repository import PlanRepository
from neo4j import AsyncSession as Neo4jSession

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

    async def add(self, step: PlanDayStepCreate):
        step = await self._refactor_step(step)
        
        plan = await self.plan_repository.get(step.plan_id, load_relations=["start_city", "unordered_days.unordered_steps"])   
        
        previous_step = await self.repository.get_by_fields({"next_plan_day_step_id": step.next_plan_day_step_id})
        next_step = await self.repository.get(step.next_plan_day_step_id)

        # Get plan and city context
        prev_step_city_id = previous_step.city_id if previous_step else plan.start_city_id
        next_step_city_id = next_step.city_id if next_step else None

        steps_to_add = []

        # Handle different step insertion scenarios
        if step.category == PlanDayStepCategoryEnum.transport:
            if prev_step_city_id == step.city_id or (next_step_city_id and step.city_id == next_step_city_id):
                return  # No transport needed

            if next_step_city_id and next_step_city_id != step.city_id and next_step.category == PlanDayStepCategoryEnum.transport:
                await self._remove_step_from_global_chain(next_step.id, next_step.next_plan_day_step_id)
                next_step = await self.repository.get(next_step.next_plan_day_step_id)

            steps_to_add.append(step)
            
            if next_step_city_id:
                steps_to_add.append(PlanDayStepCreate(
                    plan_id = step.plan_id,
                    plan_day_id=next_step.plan_day_id if (next_step and next_step.category == PlanDayStepCategoryEnum.transport) else step.plan_day_id,
                    category=PlanDayStepCategoryEnum.transport,
                    city_id=next_step_city_id
                ))

        elif step.city_id == prev_step_city_id:
            steps_to_add.append(step)
        
        else:
            if next_step and next_step.category == PlanDayStepCategoryEnum.transport:
                await self._remove_step_from_global_chain(next_step.id, next_step.next_plan_day_step_id)
                next_step = await self.repository.get(next_step.next_plan_day_step_id)
            
            steps_to_add.append(PlanDayStepCreate(
                plan_id = step.plan_id,
                plan_day_id=step.plan_day_id,
                category=PlanDayStepCategoryEnum.transport,
                city_id=step.city_id
            ))
            steps_to_add.append(step)

            if next_step_city_id and next_step_city_id != step.city_id:
                steps_to_add.append(PlanDayStepCreate(
                    plan_id = step.plan_id,
                    plan_day_id=next_step.plan_day_id if (next_step and next_step.category == PlanDayStepCategoryEnum.transport) else step.plan_day_id,
                    category=PlanDayStepCategoryEnum.transport,
                    city_id=next_step_city_id
                ))

        # Insert new steps into the global chain
        current_prev_step = previous_step
        current_prev_city_id = prev_step_city_id
        created_steps = []

        for i, step_to_add in enumerate(steps_to_add):
            step_details = await get_step_details(self.db, self.graph_db, current_prev_city_id, step_to_add)
            step_title = await get_step_title(self.db, step_to_add, current_prev_city_id)
            
            next_step_for_this = None
            if i == len(steps_to_add) - 1:  
                next_step_for_this = next_step
            else:
                next_step_for_this = None  
            
            step_internal = PlanDayStepCreateInternal(
                plan_day_id=step_to_add.plan_day_id,
                title=step_title,
                category=step_to_add.category,
                duration=step_details["duration"],
                cost=step_details["cost"],
                image_id=step_details["image"].id if step_details["image"] else None,
                place_id=step_to_add.place_id,
                city_id=step_to_add.city_id,
                place_activity_id=step_to_add.place_activity_id,
                next_plan_day_step_id=next_step_for_this.id if next_step_for_this else None
            )
            
            step_db = await self.repository.create(step_internal)
            created_steps.append(step_db)
            
            if current_prev_step:
                await self.repository.update_from_dict(current_prev_step.id, {"next_plan_day_step_id": step_db.id})
            
            if i > 0:
                await self.repository.update_from_dict(created_steps[i-1].id, {"next_plan_day_step_id": step_db.id})
            
            if step_to_add.category == PlanDayStepCategoryEnum.transport:
                await self._create_transport_route_hops(step_db, current_prev_city_id, step_to_add.city_id)

            current_prev_step = step_db
            current_prev_city_id = step_to_add.city_id

        return created_steps[0] if created_steps else None

    async def delete(self, step_id: int, force=False):
        step = await self.repository.get(step_id, load_relations=["plan_day.plan", "next_plan_day_step"])
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        plan = step.plan_day.plan
        can_delete = await PlanDayStepService._can_delete_step(self.db, step.id) if not force else True
        if not can_delete:
            raise HTTPException(status_code=400, detail="Can't delete this step.")

        if step.category != PlanDayStepCategoryEnum.transport:
            await self._remove_step_from_global_chain(step.id, step.next_plan_day_step_id)
            return True

        # Transport step deletion logic
        next_step = step.next_plan_day_step

        if not next_step:
            await self._remove_step_from_global_chain(step.id, step.next_plan_day_step_id)
            return True

        previous_step = await self.repository.get_by_fields({"next_plan_day_step_id": step.id})
        if next_step.category == PlanDayStepCategoryEnum.transport:
            prev_step_city = previous_step.city_id if previous_step else plan.start_city_id
            
            if prev_step_city == next_step.city_id:
                await self._remove_step_from_global_chain(step.id, step.next_plan_day_step_id)
                await self._remove_step_from_global_chain(step.id, step.next_plan_day_step_id)
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
                await self.plan_route_hop_repository.clear_all(next_step.id)
                await self._create_transport_route_hops(next_step, prev_step_city, next_step.city_id)
                await self._remove_step_from_global_chain(step.id, step.next_plan_day_step_id)
        else:
            raise HTTPException(status_code=400, detail="Can't delete transport step that leads to visit or activity")

        return True

    async def reorder(self, step_id: int, next_step_id: Optional[int] = None):
        step = await self.repository.get(step_id, load_relations=["plan_day.plan", "next_plan_day_step"])
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")

        target_day_id = None
        if next_step_id:
            next_step = await self.repository.get(next_step_id)
            target_day_id = next_step.plan_day_id

        can_delete = await PlanDayStepService._can_delete_step(self.db, step.id)
        if not can_delete:
            raise HTTPException(status_code=400, detail="Can't reorder this step.")
                
        step_create = PlanDayStepCreate(
            plan_id=step.plan_day.plan_id,
            plan_day_id=target_day_id,
            category=step.category,
            place_id=step.place_id,
            place_activity_id=step.place_activity_id,
            city_id=step.city_id,
            next_plan_day_step_id=next_step_id
        )
        

        await self.delete(step_id)
        return await self.add(step_create)
    
    
    async def handle_change_start_city(self, plan_id, start_city_id):
        """Handle when the plan's start city changes"""
        plan = await self.plan_repository.get(plan_id, load_relations=["days.steps"])
        
        first_step = await self.repository.get_by_fields({"plan_id": plan_id, "previous_plan_day_step_id": None}, load_relations=["previous_plan_day_step", "next_plan_day_step"])
        
        if not first_step:
            return True

        if first_step.city_id != start_city_id and first_step.category != PlanDayStepCategoryEnum.transport:
            transport_step = PlanDayStepCreate(
                plan_id=plan_id,
                plan_day_id=first_step.plan_day_id,
                category=PlanDayStepCategoryEnum.transport,
                city_id=first_step.city_id,
                next_plan_day_id=first_step.id
            )
            
            step_details = await get_step_details(self.db, self.graph_db, start_city_id, transport_step)
            step_title = await get_step_title(self.db, transport_step, start_city_id)
            
            step_internal = PlanDayStepCreateInternal(
                plan_day_id=transport_step.plan_day_id,
                title=step_title,
                category=transport_step.category,
                duration=step_details["duration"],
                cost=step_details["cost"],
                image_id=step_details["image"].id if step_details["image"] else None,
                place_id=transport_step.place_id,
                city_id=transport_step.city_id,
                place_activity_id=transport_step.place_activity_id,
                previous_plan_day_step_id=None,  
                next_plan_day_step_id=first_step.id
            )
            
            step_db = await self.repository.create(step_internal)
            await self.repository.update_from_dict(first_step.id, {"previous_plan_day_step_id": step_db.id})
            await self._create_transport_route_hops(step_db, start_city_id, transport_step.city_id)

        elif first_step.city_id == start_city_id and first_step.category == PlanDayStepCategoryEnum.transport:
            await self._remove_step_from_global_chain(first_step.id, first_step.next_plan_day_step_id)

        elif first_step.category == PlanDayStepCategoryEnum.transport:
            step_db = await self.repository.get(first_step.id)
            await self.plan_route_hop_repository.clear_all(step_db.id)
            
            step_details = await get_step_details(self.db, self.graph_db, start_city_id, first_step)
            title = await get_step_title(self.db, first_step, start_city_id)
            
            await self.repository.update_from_dict(step_db.id, {
                "duration": step_details["duration"],
                "cost": step_details["cost"],
                "image_id": step_details["image"].id if step_details["image"] else None,
                "title": title
            })
            
            await self._create_transport_route_hops(step_db, start_city_id, first_step.city_id)

    async def _remove_step_from_global_chain(self, step_id, next_step_id: int = None):
        previous_step = await self.repository.get_by_fields({"next_plan_day_step_id": step_id})

        if previous_step:
            await self.repository.update_from_dict(
                previous_step.id, 
                {"next_plan_day_step_id": next_step_id}
            )
        await self.repository.delete(step_id)

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
    async def _can_delete_step(db, step_id: int):
        """Check if a step can be deleted"""
        repo = PlanDayStepRepository(db)
        step = await repo.get(step_id, load_relations=["next_plan_day_step"])
        if step.category != PlanDayStepCategoryEnum.transport:
            return True
        
        next_step = step.next_plan_day_step
        if not next_step:
            return True
        
        if next_step.category == PlanDayStepCategoryEnum.transport:
            return True
        else:
            return False  # transport → non-transport: can't delete
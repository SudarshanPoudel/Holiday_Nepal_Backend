from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from typing import List, Optional

from app.modules.cities.graph import CityGraphRepository
from app.modules.cities.repository import CityRepository
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day_steps.graph import (
    PlanDayPlanDayStepEdge, PlanDayStepActivityEdge, PlanDayStepGraphRepository, 
    PlanDayStepNode, PlanDayStepPlaceEdge, PlanDayStepPlanDayStepEdge
)
from app.modules.plan_day_steps.repository import PlanDayStepRepositary
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayStepCreateInternal
from app.modules.plan_route_hops.graph import (
    PlanDayStepPlanRouteHopEdge, PlanRouteHopGraphRepository, PlanRouteHopCityEdge, 
    PlanRouteHopNode, PlanRouteHopPlanRouteHopEdge
)
from app.modules.plan_route_hops.repository import PlanRouteHopsRepository
from app.modules.plan_route_hops.schema import PlanRouteHopCreate
from app.modules.plan_day_steps.utils import get_step_details, get_current_city_id, get_destination_city_id, get_step_title
from app.modules.transport_route.graph import TransportRouteEdge
from app.modules.transport_route.repository import TransportRouteRepository


class PlanDayStepService:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = PlanDayStepRepositary(db)
        self.graph_repository = PlanDayStepGraphRepository(graph_db)
        self.place_repository = PlaceRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.city_graph_repository = CityGraphRepository(graph_db)
        self.city_repository = CityRepository(db)
        self.plan_route_hop_repository = PlanRouteHopsRepository(db)
        self.plan_route_hop_graph_repository = PlanRouteHopGraphRepository(graph_db)
        self.transport_route_repository = TransportRouteRepository(db)
        self.place_activity_repository = PlaceActivityRepository(db)

    async def add_step_to_plan(self, plan, step: PlanDayStepCreate, insert_in_graph: bool = True) -> List:
        """Add a step to the plan, automatically adding transport if needed"""
        latest_day, last_step = self._get_plan_context(plan)
        step = await self._refactor_step(step)
        
        steps_to_create = []
        
        # Check if transport step is needed
        if step.category != PlanDayStepCategoryEnum.transport:
            current_city_id = await get_current_city_id(plan)
            destination_city_id = await get_destination_city_id(self.db, step)
            
            if destination_city_id != current_city_id:
                transport_step = PlanDayStepCreate(
                    plan_id=latest_day.plan_id,
                    category=PlanDayStepCategoryEnum.transport,
                    end_city_id=destination_city_id
                )
                steps_to_create.append(transport_step)
        
        # Add the requested step
        steps_to_create.append(step)
        
        # Create all steps in sequence
        created_steps = []
        current_last_step = last_step
        
        for step_data in steps_to_create:
            created_step = await self._create_step(step_data, latest_day, current_last_step, insert_in_graph)
            created_steps.append(created_step)
            current_last_step = created_step  # Update for next iteration
            
            # Add to plan cost
            plan.estimated_cost += created_step.cost
        
        return created_steps

    async def delete_last_step_from_plan(self, plan, insert_in_graph: bool = True) -> None:
        """Delete the last step from the plan"""
        latest_day, last_step = self._get_plan_context(plan)
        
        if not latest_day.steps:
            raise HTTPException(status_code=403, detail="This day doesn't contain any steps.")
        
        step_id = latest_day.steps[-1].id
        await self.repository.delete(step_id)
        
        if insert_in_graph:
            await self.graph_repository.delete(step_id)

    def _get_plan_context(self, plan):
        """Get plan context (latest day and last step)"""
        if not plan.days:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        
        latest_day = plan.days[-1]
        last_step = self._get_last_step(plan.days)
        
        return latest_day, last_step
    
    async def _refactor_step(self, step: PlanDayStepCreate):
        """Clean up step data based on category"""
        if step.category == PlanDayStepCategoryEnum.transport:
            step.place_id = None
            step.place_activity_id = None
        elif step.category == PlanDayStepCategoryEnum.visit:
            step.place_activity_id = None
            step.end_city_id = None
        elif step.category == PlanDayStepCategoryEnum.activity:
            step.place_id = None
            step.end_city_id = None
        return step

    def _get_last_step(self, days):
        """Get the last step from all days"""
        for day in reversed(days):
            if day.steps:
                return day.steps[-1]
        return None

    async def _create_step(self, step_data: PlanDayStepCreate, latest_day, last_step, insert_in_graph: bool):
        """Create a step with proper indexing and connections"""
        # Calculate proper index
        step_index = last_step.index + 1 if last_step else 0
        
        # Validate and infer for transport step
        inferred_start_city_id = None
        if step_data.category == PlanDayStepCategoryEnum.transport:
            if not step_data.end_city_id:
                raise HTTPException(status_code=400, detail="Transport steps require end_city_id")
            # Get current city from the plan object passed to service
            from app.modules.plans.repository import PlanRepository
            plan_repo = PlanRepository(self.db)
            plan = await plan_repo.get(step_data.plan_id)
            inferred_start_city_id = await get_current_city_id(plan)

        # Get step details
        step_details = await get_step_details(self.db, self.graph_db, inferred_start_city_id, step_data)
        title = await get_step_title(self.db, step_data, inferred_start_city_id)

        # Build internal create schema
        step_internal = PlanDayStepCreateInternal(
            plan_day_id=latest_day.id,
            title=title,
            category=step_data.category,
            duration=step_details["duration"],
            cost=step_details["cost"],
            image_id=step_details["image"].id if step_details["image"] else None,
            place_id=step_data.place_id,
            start_city_id=inferred_start_city_id,
            end_city_id=step_data.end_city_id,
            index=step_index,
            place_activity_id=step_data.place_activity_id
        )

        # Save to DB
        step_db = await self.repository.create(step_internal)
        
        # Create graph connections if requested
        if insert_in_graph:
            await self._create_step_graph_node(step_db)
            await self._create_category_specific_connections(step_db, step_data)
            await self._connect_step_to_previous(step_db, last_step, latest_day)
            
            # Handle transport-specific route hops
            if step_data.category == PlanDayStepCategoryEnum.transport:
                await self._create_transport_route_hops(step_db, inferred_start_city_id, step_data.end_city_id)

        return step_db

    async def _create_step_graph_node(self, step_db):
        """Create graph node for the step"""
        await self.graph_repository.create(PlanDayStepNode(
            id=step_db.id, 
            category=step_db.category, 
            duration=step_db.duration, 
            cost=step_db.cost, 
            index=step_db.index
        ))

    async def _create_category_specific_connections(self, step_db, step_data):
        """Create connections specific to step category"""
        if step_data.category == PlanDayStepCategoryEnum.visit:
            await self.graph_repository.add_edge(PlanDayStepPlaceEdge(
                source_id=step_db.id, 
                target_id=step_db.place_id, 
                cost=step_db.cost, 
                duration=step_db.duration
            ))
        
        elif step_data.category == PlanDayStepCategoryEnum.activity:
            place_activity = await self.place_activity_repository.get(step_data.place_activity_id)
            await self.graph_repository.add_edge(PlanDayStepActivityEdge(
                source_id=step_db.id, 
                target_id=place_activity.activity_id, 
                cost=step_db.cost, 
                duration=step_db.duration
            ))

    async def _connect_step_to_previous(self, step_db, last_step, latest_day):
        """Connect a step to the previous step or day"""
        if last_step:
            await self.graph_repository.add_edge(PlanDayStepPlanDayStepEdge(
                source_id=last_step.id, 
                target_id=step_db.id
            ))
        else:
            await self.graph_repository.add_edge(PlanDayPlanDayStepEdge(
                source_id=latest_day.id, 
                target_id=step_db.id
            ))

    async def _create_transport_route_hops(self, step_db, start_city_id: int, end_city_id: int):
        """Create route hops for a transport step"""
        route_to_follow = await self.city_graph_repository.shortest_path(
            start_city_id, 
            end_city_id, 
            edge_type=TransportRouteEdge, 
            weight_property="distance"
        )
        if not route_to_follow:
            raise HTTPException(status_code=404, detail="No route found")
        
        last_hop_id = None
        for i, (route_id, destination_city_id) in enumerate(route_to_follow):
            hop_db = await self._create_route_hop(step_db.id, i, route_id, destination_city_id)
            await self._create_route_hop_graph_node(hop_db, route_id, i)
            await self._connect_route_hop(hop_db, last_hop_id, step_db.id)
            last_hop_id = hop_db.id

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

    async def _create_route_hop_graph_node(self, hop_db, route_id: int, index: int):
        """Create graph node for route hop"""
        route = await self.transport_route_repository.get(route_id)
        await self.plan_route_hop_graph_repository.create(PlanRouteHopNode(
            id=hop_db.id, 
            index=index, 
            route_id=hop_db.route_id, 
            route_category=route.route_category, 
            segment_duration=route.average_duration, 
            segment_cost=route.average_cost
        ))
        await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopCityEdge(
            source_id=hop_db.id, 
            target_id=hop_db.destination_city_id
        ))

    async def _connect_route_hop(self, hop_db, last_hop_id, step_id: int):
        """Connect route hop to previous hop or step"""
        if last_hop_id is None:
            await self.graph_repository.add_edge(PlanDayStepPlanRouteHopEdge(
                source_id=step_id, 
                target_id=hop_db.id
            ))
        else:
            await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopPlanRouteHopEdge(
                source_id=last_hop_id, 
                target_id=hop_db.id
            ))
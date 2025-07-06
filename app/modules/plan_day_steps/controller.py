from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.address.graph import MunicipalityGraphRepository
from app.modules.address.repository import MunicipalityRepository
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.places.repository import PlaceRepository
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day_steps.graph import PlanDayPlanDayStepEdge, PlanDayStepActivityEdge, PlanDayStepGraphRepository, PlanDayStepNode, PlanDayStepPlaceEdge, PlanDayStepPlanDayStepEdge
from app.modules.plan_day_steps.repository import PlanDayStepRepositary
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayStepCreateInternal, PlanDayStepRead
from app.modules.plan_route_hops.graph import PlanDayStepPlanRouteHopEdge, PlanRouteHopGraphRepository, PlanRouteHopMunicipalityEdge, PlanRouteHopNode, PlanRouteHopPlanRouteHopEdge
from app.modules.plan_route_hops.repository import PlanRouteHopsRepository
from app.modules.plan_route_hops.schema import PlanRouteHopCreate
from app.modules.plans.repository import PlanRepository
from app.modules.plan_day_steps.utils import PlanDayStepUtils
from app.modules.transport_route.graph import TransportRouteEdge
from app.modules.transport_route.repository import TransportRouteRepository

class PlanDayStepController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.graph_db = graph_db
        self.user_id = user_id
        self.repository = PlanDayStepRepositary(db)
        self.graph_repository = PlanDayStepGraphRepository(graph_db)
        self.plan_repository = PlanRepository(db)
        self.place_repository = PlaceRepository(db)
        self.plan_day_repository = PlanDayRepository(db)
        self.municipality_graph_repository = MunicipalityGraphRepository(graph_db)
        self.municipality_repository = MunicipalityRepository(db)
        self.plan_route_hop_repository = PlanRouteHopsRepository(db)
        self.plan_route_hop_graph_repository = PlanRouteHopGraphRepository(graph_db)
        self.transport_route_repository = TransportRouteRepository(db)
        self.place_activity_repository = PlaceActivityRepository(db)
        self.utils = PlanDayStepUtils(db)

    async def get(self, plan_day_step_id: int):
        plan_day_step = await self.repository.get(plan_day_step_id)
        if not plan_day_step:
            raise HTTPException(status_code=404, detail="Plan day step not found")
        return BaseResponse(message="Plan day step found", data=PlanDayStepRead.model_validate(plan_day_step, from_attributes=True))
   
    async def add_plan_day_step(self, step: PlanDayStepCreate):
        plan = await self.plan_repository.get(step.plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        
        latest_day = plan.days[-1]
        last_step = None
        if len(latest_day.steps) > 0:
            last_step = latest_day.steps[-1]
        elif len(plan.days) > 1:
            last_step = plan.days[-2].steps[-1]
        
        current_municipality_id = await self.utils.get_curret_municipality_id(plan)
        
        # Check if we need to add automatic transport step
        needs_transport = False
        destination_municipality_id = None
        
        if step.category == PlanDayStepCategoryEnum.visit:
            place = await self.place_repository.get(step.place_id)
            if not place:
                raise HTTPException(status_code=404, detail="Place not found")
            destination_municipality_id = place.municipality_id
            if current_municipality_id != destination_municipality_id:
                needs_transport = True
        
        elif step.category == PlanDayStepCategoryEnum.activity:
            place_activity = await self.place_activity_repository.get(step.place_activity_id, load_relations=['place'])
            if not place_activity:
                raise HTTPException(status_code=404, detail="Place activity not found")
            destination_municipality_id = place_activity.place.municipality_id
            if current_municipality_id != destination_municipality_id:
                needs_transport = True
        
        steps_created = []
        
        # Add transport step if needed
        if needs_transport:
            transport_step = await self._create_transport_step(
                latest_day, 
                last_step, 
                current_municipality_id, 
                destination_municipality_id
            )
            steps_created.append(transport_step)
            last_step = transport_step
        
        # Add the requested step
        requested_step = await self._create_requested_step(step, latest_day, last_step)
        steps_created.append(requested_step)
        
        return BaseResponse(
            message="Day step(s) added successfully", 
            data={"steps_created": [{"id": s.id, "title": s.title} for s in steps_created]}
        )

    async def _create_transport_step(self, latest_day, last_step, start_municipality_id, end_municipality_id):
        """Create and save a transport step"""
        # Create transport step data
        transport_step_data = type('TransportStepData', (), {
            'category': PlanDayStepCategoryEnum.transport,
            'end_municipality_id': end_municipality_id
        })()
        
        duration = await self.utils.get_step_duration(transport_step_data)
        cost = await self.utils.get_step_cost()
        time_frame = await self.utils.get_step_time_frame(latest_day, duration)
        image_id = await self.utils.get_step_image()
        
        municipality_start = await self.municipality_repository.get(start_municipality_id)
        municipality_end = await self.municipality_repository.get(end_municipality_id)
        title = f"Travel From {municipality_start.name} to {municipality_end.name}"
        
        step_index = last_step.index + 1 if last_step else 0
        
        step_internal = PlanDayStepCreateInternal(
            plan_day_id=latest_day.id,
            title=title,
            category=PlanDayStepCategoryEnum.transport,
            time_frame=time_frame,
            duration=duration,
            cost=cost,
            image_id=image_id,
            place_id=None,
            start_municipality_id=start_municipality_id,
            end_municipality_id=end_municipality_id,
            index=step_index,
            place_activity_id=None
        )
        
        step_db = await self.repository.create(step_internal)
        await self.graph_repository.create(PlanDayStepNode(
            id=step_db.id, 
            category=step_db.category, 
            time_frame=step_db.time_frame, 
            duration=step_db.duration, 
            cost=step_db.cost, 
            index=step_db.index
        ))
        
        # Handle transport route logic
        route_to_follow = await self.municipality_graph_repository.shortest_path(
            start_municipality_id, 
            end_municipality_id, 
            edge_type=TransportRouteEdge, 
            weight_property="distance"
        )
        if not route_to_follow:
            raise HTTPException(status_code=404, detail="No route found")
        
        last_hop_id = None
        for i, (route_id, destination_municipality_id) in enumerate(route_to_follow):
            plan_route_hop = await self.plan_route_hop_repository.create(
                PlanRouteHopCreate(
                    plan_day_step_id=step_db.id,
                    index=i,
                    route_id=route_id,
                    destination_municipality_id=destination_municipality_id
                )
            )
            route = await self.transport_route_repository.get(route_id)
            await self.plan_route_hop_graph_repository.create(PlanRouteHopNode(
                id=plan_route_hop.id, 
                index=i, 
                route_id=plan_route_hop.route_id, 
                route_category=route.route_category, 
                segment_duration=route.average_duration, 
                segment_cost=route.average_cost
            ))
            await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopMunicipalityEdge(
                source_id=plan_route_hop.id, 
                target_id=plan_route_hop.destination_municipality_id
            ))
            if last_hop_id is None:
                await self.graph_repository.add_edge(PlanDayStepPlanRouteHopEdge(
                    source_id=step_db.id, 
                    target_id=plan_route_hop.id
                ))
            else:
                await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopPlanRouteHopEdge(
                    source_id=last_hop_id, 
                    target_id=plan_route_hop.id
                ))
            last_hop_id = plan_route_hop.id
        
        # Connect to previous step or day
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
        
        return step_db

    async def _create_requested_step(self, step, latest_day, last_step):
        """Create and save the requested step (visit/activity/transport)"""
        duration = await self.utils.get_step_duration(step)
        cost = await self.utils.get_step_cost()
        time_frame = await self.utils.get_step_time_frame(latest_day, duration)
        image_id = await self.utils.get_step_image()

        place_id = None
        start_municipality_id = None
        end_municipality_id = None
        place_activity_id = None
        title = None
        
        if step.category == PlanDayStepCategoryEnum.transport:
            current_municipality_id = await self.utils.get_curret_municipality_id(plan)
            start_municipality_id = current_municipality_id
            end_municipality_id = step.end_municipality_id
            municipality_start = await self.municipality_repository.get(start_municipality_id)
            municipality_end = await self.municipality_repository.get(end_municipality_id)
            title = f"Travel From {municipality_start.name} to {municipality_end.name}"
        
        elif step.category == PlanDayStepCategoryEnum.visit:
            place_id = step.place_id
            place = await self.place_repository.get(place_id)
            title = f"Visit {place.name}"
        
        elif step.category == PlanDayStepCategoryEnum.activity:
            place_activity_id = step.place_activity_id
            activity = await self.place_activity_repository.get(step.place_activity_id, load_relations=['place', 'activity'])
            title = f"Do {activity.activity.name} at {activity.place.name}"

        step_index = last_step.index + 1 if last_step else 0
        
        step_internal = PlanDayStepCreateInternal(
            plan_day_id=latest_day.id,
            title=title,
            category=step.category,
            time_frame=time_frame,
            duration=duration,
            cost=cost,
            image_id=image_id,
            place_id=place_id,
            start_municipality_id=start_municipality_id,
            end_municipality_id=end_municipality_id,
            index=step_index,
            place_activity_id=place_activity_id
        )
        
        step_db = await self.repository.create(step_internal)
        await self.graph_repository.create(PlanDayStepNode(
            id=step_db.id, 
            category=step_db.category, 
            time_frame=step_db.time_frame, 
            duration=step_db.duration, 
            cost=step_db.cost, 
            index=step_db.index
        ))
        
        # Handle category-specific logic
        if step.category == PlanDayStepCategoryEnum.transport:
            # This is a manually requested transport step
            route_to_follow = await self.municipality_graph_repository.shortest_path(
                start_municipality_id, 
                end_municipality_id, 
                edge_type=TransportRouteEdge, 
                weight_property="distance"
            )
            if not route_to_follow:
                raise HTTPException(status_code=404, detail="No route found")
            
            last_hop_id = None
            for i, (route_id, destination_municipality_id) in enumerate(route_to_follow):
                plan_route_hop = await self.plan_route_hop_repository.create(
                    PlanRouteHopCreate(
                        plan_day_step_id=step_db.id,
                        index=i,
                        route_id=route_id,
                        destination_municipality_id=destination_municipality_id
                    )
                )
                route = await self.transport_route_repository.get(route_id)
                await self.plan_route_hop_graph_repository.create(PlanRouteHopNode(
                    id=plan_route_hop.id, 
                    index=i, 
                    route_id=plan_route_hop.route_id, 
                    route_category=route.route_category, 
                    segment_duration=route.average_duration, 
                    segment_cost=route.average_cost
                ))
                await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopMunicipalityEdge(
                    source_id=plan_route_hop.id, 
                    target_id=plan_route_hop.destination_municipality_id
                ))
                if last_hop_id is None:
                    await self.plan_day_step_graph_repository.add_edge(PlanDayStepPlanRouteHopEdge(
                        source_id=step_db.id, 
                        target_id=plan_route_hop.id
                    ))
                else:
                    await self.plan_route_hop_graph_repository.add_edge(PlanRouteHopPlanRouteHopEdge(
                        source_id=last_hop_id, 
                        target_id=plan_route_hop.id
                    ))
                last_hop_id = plan_route_hop.id

        elif step.category == PlanDayStepCategoryEnum.visit:
            await self.graph_repository.add_edge(PlanDayStepPlaceEdge(
                source_id=step_db.id, 
                target_id=step_db.place_id, 
                cost=step_db.cost, 
                duration=step_db.duration
            ))
        
        elif step.category == PlanDayStepCategoryEnum.activity:
            activity = await self.place_activity_repository.get(step.place_activity_id)
            await self.graph_repository.add_edge(PlanDayStepActivityEdge(
                source_id=step_db.id, 
                target_id=activity.activity_id, 
                cost=step_db.cost, 
                duration=step_db.duration
            ))
        
        # Connect to previous step or day
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
        
        return step_db


    async def delete_day_step(self, plan_id: int):
        plan = await self.plan_repository.get(plan_id, load_relations=["days.steps"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.user_id != self.user_id:
            raise HTTPException(status_code=403, detail="You can only update your plans")
        if len(plan.days) <= 0:
            raise HTTPException(status_code=403, detail="This plan doesn't contain any days.")
        if len(plan.days[-1].steps) <= 0:
            raise HTTPException(status_code=403, detail="This day doesn't contain any steps.")
        
        step_id = plan.days[-1].steps[-1].id
        await self.repository.delete(step_id)
        await self.graph_repository.delete(step_id)
        return BaseResponse(message="Day step deleted successfully")
        
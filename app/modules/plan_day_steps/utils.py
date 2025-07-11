from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.places.utils import get_place_image
from app.modules.places.repository import PlaceRepository
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.cities.repository import CityRepository
from app.modules.cities.graph import CityGraphRepository
from app.modules.transport_route.repository import TransportRouteRepository
from app.modules.transport_route.graph import TransportRouteEdge
from app.modules.plan_day.models import PlanDay
from app.modules.plan_day.schema import PlanDayRead
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayStepRead, PlanDayTimeFrameEnum
from app.modules.plans.models import Plan
from app.modules.storage.repository import ImageRepository
from app.modules.storage.schema import ImageRead
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_service.utils import get_image_from_transport_service_category
from neo4j import AsyncSession as Neo4jSession


async def get_step_time_frame(db: AsyncSession, day: PlanDayRead, step_duration: float) -> PlanDayTimeFrameEnum:
    """Calculate time frame for a step based on the day and duration"""
    BASE_START_HOUR = 8  # 8 AM
    step_count = len(day.steps)
    total_existing_duration = sum(step.duration or 1 for step in day.steps if step.duration)
    total_gap_time = max(0, step_count)  # 1 hour gap between each existing step
    starting_hour = BASE_START_HOUR + total_existing_duration + total_gap_time
    step_duration = step_duration or 1
    ending_hour = starting_hour + step_duration
    duration = ending_hour - starting_hour
    
    # Full day if long or spans multiple time ranges
    if duration >= 6 or \
       (starting_hour < 5 <= ending_hour) or \
       (starting_hour < 12 <= ending_hour) or \
       (starting_hour < 17 <= ending_hour) or \
       (starting_hour < 21 <= ending_hour):
        return PlanDayTimeFrameEnum.night #TODO: fix it
    if 5 <= starting_hour < 12:
        return PlanDayTimeFrameEnum.morning
    elif 12 <= starting_hour < 17:
        return PlanDayTimeFrameEnum.afternoon
    elif 17 <= starting_hour < 21:
        return PlanDayTimeFrameEnum.evening
    else:
        return PlanDayTimeFrameEnum.night


async def get_step_details(db: AsyncSession, graph_db: Neo4jSession, current_city_id: int, step: PlanDayStepCreate) -> dict:
    """
    Get step details (duration, cost, image) from a PlanDayStepCreate object
    by loading all required relations from the database
    """
    duration, cost = 0, 0
    image = None
    
    # Initialize repositories
    place_repo = PlaceRepository(db)
    place_activity_repo = PlaceActivityRepository(db)
    city_repo = CityRepository(db)
    city_graph_repo = CityGraphRepository(graph_db)
    transport_route_repo = TransportRouteRepository(db)
    
    if step.category == PlanDayStepCategoryEnum.visit:
        if not step.place_id:
            raise ValueError("place_id is required for visit steps")
        
        # Load place from database
        place = await place_repo.get(step.place_id)
        if not place:
            raise ValueError(f"Place with id {step.place_id} not found")
        
        duration = place.average_visit_duration
        cost = place.average_visit_cost
        image = await get_place_image(db, place.id)
    
    elif step.category == PlanDayStepCategoryEnum.activity:
        if not step.place_activity_id:
            raise ValueError("place_activity_id is required for activity steps")
        
        # Load place activity with relations
        place_activity = await place_activity_repo.get(
            step.place_activity_id, 
            load_relations=['place', 'activity.image']
        )
        if not place_activity:
            raise ValueError(f"Place activity with id {step.place_activity_id} not found")
        
        duration = place_activity.average_duration
        cost = place_activity.average_cost
        image = place_activity.activity.image
    
    elif step.category == PlanDayStepCategoryEnum.transport:
        # For transport steps, we need to calculate route
        start_city_id = current_city_id
        end_city_id = getattr(step, 'end_city_id', None)
        
        if not start_city_id or not end_city_id:
            raise ValueError("start_city_id and end_city_id are required for transport steps")
        
        # Get shortest path between cities
        route_to_follow = await city_graph_repo.shortest_path(
            start_city_id, 
            end_city_id, 
            edge_type=TransportRouteEdge, 
            weight_property="distance"
        )
        
        if not route_to_follow:
            raise ValueError(f"No route found from city {start_city_id} to city {end_city_id}")
        
        # Calculate total duration and cost from route hops
        for route_id, destination_city_id in route_to_follow:
            route = await transport_route_repo.get(route_id)
            if route:
                duration += route.average_duration
                cost += route.average_cost
        
        # Get transport image (defaulting to bus for now)
        image = await get_image_from_transport_service_category(db, TransportServiceCategoryEnum.bus)
    
    else:
        raise ValueError(f"Unknown step category: {step.category}")
    
    return {
        "duration": duration,
        "cost": cost,
        "image": image
    }


async def get_step_title(db: AsyncSession, step: PlanDayStepCreate, current_city_id: int) -> str:
    """Generate appropriate title for a step based on its category"""
    place_repo = PlaceRepository(db)
    place_activity_repo = PlaceActivityRepository(db)
    city_repo = CityRepository(db)
    
    if step.category == PlanDayStepCategoryEnum.visit:
        if not step.place_id:
            raise ValueError("place_id is required for visit steps")
        
        place = await place_repo.get(step.place_id)
        if not place:
            raise ValueError(f"Place with id {step.place_id} not found")
        
        return f"Visit {place.name}"
    
    elif step.category == PlanDayStepCategoryEnum.activity:
        if not step.place_activity_id:
            raise ValueError("place_activity_id is required for activity steps")
        
        place_activity = await place_activity_repo.get(
            step.place_activity_id, 
            load_relations=['place', 'activity']
        )
        if not place_activity:
            raise ValueError(f"Place activity with id {step.place_activity_id} not found")
        
        return f"Do {place_activity.activity.name} at {place_activity.place.name}"
    
    elif step.category == PlanDayStepCategoryEnum.transport:
        start_city_id = current_city_id
        end_city_id = getattr(step, 'end_city_id', None)
        
        if not start_city_id or not end_city_id:
            raise ValueError("start_city_id and end_city_id are required for transport steps")
        
        city_start = await city_repo.get(start_city_id)
        city_end = await city_repo.get(end_city_id)
        
        if not city_start or not city_end:
            raise ValueError("Start or end city not found")
        
        return f"Travel From {city_start.name} to {city_end.name}"
    
    else:
        raise ValueError(f"Unknown step category: {step.category}")


async def get_current_city_id(plan: Plan) -> int:
    """Get the current city ID from the plan (last step's end_city_id or plan's start_city_id)"""
    for plan_day in reversed(plan.days):
        for step in reversed(plan_day.steps):
            if step.end_city_id:
                return step.end_city_id
    return plan.start_city_id


async def get_destination_city_id(db: AsyncSession, step: PlanDayStepCreate) -> int:
    """Get the destination city ID for a step based on its category"""
    place_repo = PlaceRepository(db)
    place_activity_repo = PlaceActivityRepository(db)
    
    if step.category == PlanDayStepCategoryEnum.visit:
        if not step.place_id:
            raise ValueError("place_id is required for visit steps")
        
        place = await place_repo.get(step.place_id)
        if not place:
            raise ValueError(f"Place with id {step.place_id} not found")
        
        return place.city_id
    
    elif step.category == PlanDayStepCategoryEnum.activity:
        if not step.place_activity_id:
            raise ValueError("place_activity_id is required for activity steps")
        
        place_activity = await place_activity_repo.get(
            step.place_activity_id, 
            load_relations=['place']
        )
        if not place_activity:
            raise ValueError(f"Place activity with id {step.place_activity_id} not found")
        
        return place_activity.place.city_id
    
    elif step.category == PlanDayStepCategoryEnum.transport:
        end_city_id = getattr(step, 'end_city_id', None)
        if not end_city_id:
            raise ValueError("end_city_id is required for transport steps")
        
        return end_city_id
    
    else:
        raise ValueError(f"Unknown step category: {step.category}")



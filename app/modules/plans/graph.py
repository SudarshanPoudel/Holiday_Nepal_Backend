from typing import ClassVar
from neo4j import AsyncSession as Neo4jSession
from sqlalchemy.ext.asyncio import AsyncSession 
from app.core.graph_repository import BaseGraphRepository
from app.core.graph_schemas import  BaseEdge, BaseNode
from app.modules.cities.graph import CityNode
from app.modules.plans.models import Plan


class PlanNode(BaseNode):
    label: ClassVar[str] = "Plan"
    child_relationships = {"PLAN_STARTS_AT_PLAN_DAY": "PlanDay"}
    user_id: int
    no_of_people: int

class PlanCityEdge(BaseEdge):
    label: ClassVar[str] = "PLAN_STARTS_AT_CITY"
    source_model = PlanNode
    target_model = CityNode

class PlanGraphRepository(BaseGraphRepository[PlanNode]):
    def __init__(self, session: Neo4jSession):
        super().__init__(session, PlanNode)

    async def create_from_sql_model(self, plan: Plan, user_id: int, db: AsyncSession):
        from app.modules.place_activities.repository import PlaceActivityRepository
        from app.modules.plan_day.graph import PlanDayGraphRepository, PlanDayNode, PlanDayPlanDayEdge, PlanPlanDayEdge
        from app.modules.plan_day_steps.graph import PlanDayPlanDayStepEdge, PlanDayStepActivityEdge, PlanDayStepGraphRepository, PlanDayStepNode, PlanDayStepPlaceEdge, PlanDayStepPlanDayStepEdge
        from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum
        from app.modules.plan_route_hops.graph import PlanDayStepPlanRouteHopEdge, PlanRouteHopCityEdge, PlanRouteHopGraphRepository, PlanRouteHopNode, PlanRouteHopPlanRouteHopEdge
        from app.modules.transport_route.repository import TransportRouteRepository
        
        await self.create(
            PlanNode(id=plan.id, user_id=user_id, no_of_people=plan.no_of_people)
        )
        await self.add_edge(PlanCityEdge(source_id=plan.id, target_id=plan.start_city_id))

        plan_day_graph_repository = PlanDayGraphRepository(self.session)
        plan_day_step_graph_repository = PlanDayStepGraphRepository(self.session)
        plan_route_hop_graph_repository = PlanRouteHopGraphRepository(self.session)
        route_repository = TransportRouteRepository(db)
        place_activity_repository = PlaceActivityRepository(db)

        # Track processed nodes to avoid duplicates
        processed_days = set()
        processed_steps = set()
        processed_route_hops = set()

        last_day_node_id = None
        for day_index, day in enumerate(plan.days):
            if day.id in processed_days:
                continue
                
            await plan_day_graph_repository.create(PlanDayNode(id=day.id, index=day.index))
            processed_days.add(day.id)

            if not last_day_node_id:
                await self.add_edge(PlanPlanDayEdge(source_id=plan.id, target_id=day.id))
            else:
                await plan_day_graph_repository.add_edge(PlanDayPlanDayEdge(source_id=last_day_node_id, target_id=day.id))

            last_day_node_id = day.id
            last_day_step_node_id = None

            # Filter out circular references and duplicates
            valid_steps = []
            for step in day.steps:
                if isinstance(step, str) and 'CircularRef' in step:
                    continue
                if step.id not in processed_steps:
                    valid_steps.append(step)

            for step_index, step in enumerate(valid_steps):
                if step.id in processed_steps:
                    continue
                    
                await plan_day_step_graph_repository.create(
                    PlanDayStepNode(
                        id=step.id,
                        index=step.index,
                        category=step.category,
                        duration=step.duration,
                        cost=step.cost
                    )
                )
                processed_steps.add(step.id)

                if not last_day_step_node_id:
                    await plan_day_graph_repository.add_edge(PlanDayPlanDayStepEdge(source_id=day.id, target_id=step.id))
                else:
                    await plan_day_step_graph_repository.add_edge(PlanDayStepPlanDayStepEdge(source_id=last_day_step_node_id, target_id=step.id))

                last_day_step_node_id = step.id

                if step.category == PlanDayStepCategoryEnum.transport:
                    last_route_hop_id = None
                    for hop_index, route_hop in enumerate(step.route_hops):
                        # Skip if this route hop has already been processed
                        if route_hop.id in processed_route_hops:
                            continue
                            
                        route = await route_repository.get(route_hop.route_id)
                        await plan_route_hop_graph_repository.create(
                            PlanRouteHopNode(
                                id=route_hop.id,
                                index=route_hop.index,
                                route_id=route_hop.route_id,
                                route_category=route.route_category,
                                segment_duration=route.average_duration,
                                segment_cost=route.average_cost
                            )
                        )
                        processed_route_hops.add(route_hop.id)

                        await plan_route_hop_graph_repository.add_edge(
                            PlanRouteHopCityEdge(source_id=route_hop.id, target_id=route_hop.destination_city_id)
                        )

                        if not last_route_hop_id:
                            await plan_day_step_graph_repository.add_edge(
                                PlanDayStepPlanRouteHopEdge(source_id=step.id, target_id=route_hop.id)
                            )
                        else:
                            await plan_route_hop_graph_repository.add_edge(
                                PlanRouteHopPlanRouteHopEdge(source_id=last_route_hop_id, target_id=route_hop.id)
                            )

                        last_route_hop_id = route_hop.id

                elif step.category == PlanDayStepCategoryEnum.visit:
                    await plan_day_step_graph_repository.add_edge(
                        PlanDayStepPlaceEdge(source_id=step.id, target_id=step.place_id, cost=step.cost, duration=step.duration)
                    )

                elif step.category == PlanDayStepCategoryEnum.activity:
                    place_activity = await place_activity_repository.get(step.place_activity_id)
                    await plan_day_step_graph_repository.add_edge(
                        PlanDayStepActivityEdge(source_id=step.id, target_id=place_activity.activity_id)
                    )
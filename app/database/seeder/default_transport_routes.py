import json
from pathlib import Path
from sqlalchemy import select
from neo4j import AsyncSession as Neo4jSession
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import graph_repository
from app.core.all_models import Municipality, TransportRoute  # adjust import paths
from app.database.seeder.utils import load_data
from app.modules.transport_route.graph import TransportRouteEdge, TransportRouteGraphRepository
from app.modules.transport_route.schema import RouteCategoryEnum

async def seed_default_transport_routes(db: AsyncSession, graph_db: Neo4jSession):
    routes_data = load_data("files/default_transport_routes.json")
    graph_repository = TransportRouteGraphRepository(graph_db)
    for route in routes_data:
        start_name = route["start_municipality"]
        end_name = route["end_municipality"]

        # Fetch start and end municipalities
        start_result = await db.execute(select(Municipality).where(Municipality.name == start_name))
        end_result = await db.execute(select(Municipality).where(Municipality.name == end_name))

        start = start_result.scalar_one_or_none()
        end = end_result.scalar_one_or_none()

        if not start or not end:
            continue

        # Check for duplicates (same start/end/category)
        existing = await db.execute(
            select(TransportRoute).where(
                TransportRoute.start_municipality_id == start.id,
                TransportRoute.end_municipality_id == end.id,
                TransportRoute.route_category == RouteCategoryEnum(route["route_category"])
            )
        )
        if existing.scalar():
            continue
        existing_opposite = await db.execute(
            select(TransportRoute).where(
                TransportRoute.start_municipality_id == end.id,
                TransportRoute.end_municipality_id == start.id,
                TransportRoute.route_category == RouteCategoryEnum(route["route_category"])
            )
        )
        if existing_opposite.scalar():
            continue
        new_route = TransportRoute(
            start_municipality_id=start.id,
            end_municipality_id=end.id,
            route_category=RouteCategoryEnum(route["route_category"]),
            distance=route["distance"],
            average_time=route.get("average_time")
        )

        db.add(new_route)
        await db.flush()

        new_route_edge = TransportRouteEdge(id=new_route.id, start_id=start.id, end_id=end.id, route_category=RouteCategoryEnum(route["route_category"]), distance=route["distance"], average_time=route.get("average_time"))
        await graph_repository.create(new_route_edge)


    await db.commit()
    print("Default transport routes seeded.")

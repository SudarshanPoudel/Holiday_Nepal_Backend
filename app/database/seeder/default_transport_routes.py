import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.all_models import Municipality, TransportRoute  # adjust import paths
from app.modules.transport_route.schema import RouteCategoryEnum

async def seed_default_transport_routes(db: AsyncSession):
    file_path = Path("app/seeder/files/default_transport_routes.json")
    if not file_path.exists():
        print("default_transport_routes.json not found.")
        return

    with file_path.open("r", encoding="utf-8") as f:
        routes_data = json.load(f)

    for route in routes_data:
        start_name = route["start_municipality"]
        end_name = route["end_municipality"]

        # Fetch start and end municipalities
        start_result = await db.execute(select(Municipality).where(Municipality.name == start_name))
        end_result = await db.execute(select(Municipality).where(Municipality.name == end_name))

        start = start_result.scalar_one_or_none()
        end = end_result.scalar_one_or_none()

        if not start or not end:
            print(f"Skipping route {route['id']}: municipality not found")
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

        new_route = TransportRoute(
            id=route["id"],
            start_municipality_id=start.id,
            end_municipality_id=end.id,
            route_category=RouteCategoryEnum(route["route_category"]),
            distance=route["distance"],
            average_time=route.get("average_time")
        )

        db.add(new_route)

    await db.commit()
    print("Default transport routes seeded.")

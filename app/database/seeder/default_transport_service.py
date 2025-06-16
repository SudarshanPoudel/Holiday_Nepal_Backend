import json
from pathlib import Path
from sqlalchemy import select
from app.core.all_models import TransportService, TransportServiceRouteSegment, Municipality, TransportRoute, ServiceProvider, Image
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_route.schema import RouteCategoryEnum
from app.modules.storage.schema import ImageCategoryEnum

from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException
from app.modules.storage.service import StorageService 


async def seed_default_transport_services(db):
    json_path = Path("app/seeders/files/data/default_transport_services.json")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path) as f:
        transport_services = json.load(f)

    for entry in transport_services:
        provider = await db.scalar(select(ServiceProvider).join(ServiceProvider.user).where(ServiceProvider.user.has(username=entry["username"])))
        if not provider:
            print(f"ServiceProvider not found for username: {entry['username']}")
            continue

        route_ids = []
        total_distance = 0
        total_time = 0

        for segment in entry["segments"]:
            start = await db.scalar(select(Municipality).where(Municipality.name == segment["start"]))
            end = await db.scalar(select(Municipality).where(Municipality.name == segment["end"]))

            if not start or not end:
                print(f"Invalid municipality: {segment}")
                continue

            route = await db.scalar(select(TransportRoute).where(
                TransportRoute.start_municipality_id == start.id,
                TransportRoute.end_municipality_id == end.id
            ))

            if not route:
                print(f"No matching route found for {segment}")
                continue

            route_ids.append(route.id)
            total_distance += route.distance
            total_time += route.average_time or 0

        start_mun = await db.scalar(select(Municipality).where(Municipality.name == entry["segments"][0]["start"]))
        end_mun = await db.scalar(select(Municipality).where(Municipality.name == entry["segments"][-1]["end"]))

        new_service = TransportService(
            service_provider_id=provider.id,
            description=entry["description"],
            start_municipality_id=start_mun.id,
            end_municipality_id=end_mun.id,
            route_category=RouteCategoryEnum(entry["route_category"]),
            transport_category=TransportServiceCategoryEnum(entry["transport_category"]),
            total_distance=total_distance,
            average_time=total_time
        )
        db.add(new_service)
        await db.flush()

        for idx, route_id in enumerate(route_ids):
            db.add(TransportServiceRouteSegment(
                service_id=new_service.id,
                route_id=route_id,
                sequence=idx
            ))

        for path in entry.get("image_paths", []):
            file_path = Path(path)
            if not file_path.exists():
                print(f"Image not found: {file_path}")
                continue
            key = f"services/{file_path.stem}.webp"
            content = file_path.read_bytes()
            s3_service = StorageService()
            await s3_service.upload_file(key, content, "image/webp")
            url = s3_service.get_file_url(key)

            image = Image(key=key, url=url, category=ImageCategoryEnum.services)
            db.add(image)
            await db.flush()
            new_service.images.append(image)

    await db.commit()
    print("Transport services seeded.")

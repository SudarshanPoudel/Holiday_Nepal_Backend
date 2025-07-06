import json
from pathlib import Path
from sqlalchemy import insert, select
from app.core.all_models import TransportService, TransportServiceRouteSegment, Municipality, TransportRoute, ServiceProvider, Image
from app.modules.transport_service.models import transport_service_images
from app.database.seeder.utils import get_file_path, load_data
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_route.schema import RouteCategoryEnum
from app.modules.storage.schema import ImageCategoryEnum

from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException
from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image 


async def seed_default_transport_services(db):
    transport_services = load_data("files/default_transport_services.json")
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
                route = await db.scalar(select(TransportRoute).where(
                    TransportRoute.start_municipality_id == end.id,
                    TransportRoute.end_municipality_id == start.id
                ))
                if not route:
                    continue

            route_ids.append(route.id)
            total_distance += route.distance
            total_time += route.average_duration or 0

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
            average_duration=total_time
        )
        db.add(new_service)
        await db.flush()

        for idx, route_id in enumerate(route_ids):
            db.add(TransportServiceRouteSegment(
                service_id=new_service.id,
                route_id=route_id,
                index=idx
            ))

        transport_images = []
        for path in entry.get("image_paths", []):
            file_path = get_file_path(f"files/images/transport/{path}")
            key = f"services/{StorageService.generate_unique_key('webp')}"
            existing = await db.scalar(select(Image).where(Image.key == key))
            if existing:
                transport_images.append(existing)
                continue

            with open(file_path, "rb") as f:
                content = f.read()
            content = validate_and_process_image(content, resize_to=(1080, 720))
            s3_service = StorageService()
            await s3_service.upload_file(key, content, "image/webp")
            url = s3_service.get_file_url(key)

            image = Image(key=key, url=url, category=ImageCategoryEnum.services)
            db.add(image)
            await db.flush()
            transport_images.append(image)

        for image in transport_images:
            existing = await db.scalar(
                select(transport_service_images).where(
                    transport_service_images.c.transport_service_id == new_service.id, transport_service_images.c.image_id == image.id
                )
            )
            if existing:
                continue
            await db.execute(insert(transport_service_images).values(transport_service_id=new_service.id, image_id=image.id))
        

    await db.commit()
    print("Transport services seeded.")

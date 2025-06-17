import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.core.all_models import User, Municipality, AccomodationService, ServiceProvider, Image
from app.database.seeder.utils import get_file_path, load_data
from app.modules.accomodation_service.schema import AccomodationCategoryEnum
from app.modules.storage.schema import ImageCategoryEnum

from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image

async def seed_default_accomodation_services(db: AsyncSession):
    service_data = load_data("files/default_accommodation_services.json")
    for data in service_data:
        # Lookup user
        user = await db.scalar(select(User).where(User.username == data["username"]))
        if not user:
            print(f"User {data['username']} not found. Skipping.")
            continue

        # Lookup ServiceProvider
        sp = await db.scalar(select(ServiceProvider).where(ServiceProvider.user_id == user.id))
        if not sp:
            print(f"ServiceProvider for user {user.username} not found. Skipping.")
            continue

        # Lookup Municipality
        municipality = await db.scalar(select(Municipality).where(Municipality.name == data["municipality"]))
        if not municipality:
            print(f"Municipality {data['municipality']} not found. Skipping.")
            continue

        # Upload images and create image records
        images = []
        for image_name in data["images"]:
            local_path = Path(get_file_path("files/images/accomodation/" + image_name))
            if not local_path.exists():
                print(f"Image {image_name} not found. Skipping.")
                continue

            key = f"services/{StorageService.generate_unique_key('.webp')}"
            content = local_path.read_bytes()
            content = validate_and_process_image(content)
            # Upload to S3/localstack
            file_service = StorageService()
            try:
                await file_service.upload_file(key=key, file_content=content, content_type="image/webp")
            except HTTPException:
                print(f"Failed to upload {key}. Skipping.")
                continue

            image = Image(
                key=key,
                url=file_service.get_file_url(key),
                category=ImageCategoryEnum.services
            )
            db.add(image)
            await db.flush()  # to get image.id
            images.append(image)

        # Create and add AccomodationService
        service = AccomodationService(
            description=data["description"],
            service_provider_id=sp.id,
            municipality_id=municipality.id,
            full_location=data["full_location"],
            accomodation_category=AccomodationCategoryEnum(data["accomodation_category"]),
            longitude=data["longitude"],
            latitude=data["latitude"],
            cost_per_night=data["cost_per_night"],
            images=images
        )

        db.add(service)

    await db.commit()
    print("Accomodation services seeded.")

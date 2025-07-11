from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.all_models import City, AccomodationService, Image
from app.database.seeder.utils import get_file_path, load_data
from app.modules.accomodation_services.schema import AccomodationCategoryEnum
from app.modules.storage.schema import ImageCategoryEnum

from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image

async def seed_default_accomodation_services(db: AsyncSession):
    service_data = load_data("files/default_accommodation_services.json")
    for data in service_data:
        city = await db.scalar(select(City).where(City.name == data["city"]))
        if not city:
            print(f"City {data['city']} not found. Skipping.")
            continue

        # Check if the service already exists
        existing_service = await db.scalar(
            select(AccomodationService).where(
                AccomodationService.name == data["name"],
                AccomodationService.city_id == city.id
            )
        )
        if existing_service:
            continue

        # Upload images and create image records
        images = []
        for image_name in data["images"]:
            local_path = Path(get_file_path("../../../seeder-images/accomodation/" + image_name))
            if not local_path.exists():
                print(f"Image {image_name} not found. Skipping.")
                continue

            key = f"services/{StorageService.generate_unique_key('webp')}"
            content = local_path.read_bytes()
            content = validate_and_process_image(content)

            file_service = StorageService()
            await file_service.upload_file(key=key, file_content=content, content_type="image/webp")

            image = Image(
                key=key,
                category=ImageCategoryEnum.services
            )
            db.add(image)
            await db.flush()
            images.append(image)

        # Create and add AccomodationService
        service = AccomodationService(
            name=data["name"],
            description=data["description"],
            city_id=city.id,
            full_address=data["full_address"],
            accomodation_category=AccomodationCategoryEnum(data["accomodation_category"]),
            longitude=data["longitude"],
            latitude=data["latitude"],
            cost_per_night=data["cost_per_night"],
            images=images
        )

        db.add(service)

    await db.commit()
    print("Seeder: Accomodation services seeded.")

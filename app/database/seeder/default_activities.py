import json
from pathlib import Path
from slugify import slugify
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.models import Activity
from app.modules.storage.models import Image, ImageCategoryEnum
from app.modules.storage.service import StorageService  # Use your actual S3 service import

ACTIVITY_JSON_PATH = "app/seeders/data/default_activities.json"

async def seed_default_activities(db: AsyncSession):
    with open(ACTIVITY_JSON_PATH, "r") as f:
        activities = json.load(f)

    for activity in activities:
        name = activity["name"]
        slug = slugify(name)
        description = activity.get("description")
        image_path = Path(activity["image_path"])

        result = await db.execute(select(Activity).filter_by(name_slug=slug))
        if result.scalar():
            continue

        if not image_path.exists():
            print(f"Image not found: {image_path}")
            continue

        with open(image_path, "rb") as f:
            content = f.read()

        s3_key = f"activities/{slug}.webp"
        s3_service = StorageService()
        await s3_service.upload_file(key=s3_key, file_content=content, content_type="image/webp")
        image_url = s3_service.get_file_url(s3_key)

        image = Image(key=s3_key, url=image_url, category=ImageCategoryEnum.services)
        db.add(image)
        await db.flush()  # to get image.id

        db.add(Activity(
            name=name,
            name_slug=slug,
            description=description,
            image_id=image.id
        ))

    await db.commit()

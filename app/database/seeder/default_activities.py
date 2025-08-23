import json
from pathlib import Path
from app.database.seeder.utils import get_file_path, load_data
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.models import Activity
from app.modules.storage.models import Image, ImageCategoryEnum
from app.modules.storage.service import StorageService 
from app.utils.helper import slugify
from app.utils.image_utils import validate_and_process_image

async def seed_default_activities(db: AsyncSession):
    activities = load_data("files/default_activities.json")
    n = 0
    for activity in activities:
        name = activity["name"]
        description = activity.get("description")
        image_path = get_file_path(f"../../../seeder-images/activities/{activity['image']}")
        result = await db.execute(select(Activity).filter_by(name=name))
        if result.scalar():
            continue
        
        try:
            with open(image_path, "rb") as f:
                content = validate_and_process_image(f.read(), resize_to=(1080, 720))

            s3_key = f"activities/{slugify(name)}.webp"
            s3_service = StorageService()
            await s3_service.upload_file(key=s3_key, file_content=content, content_type="image/webp")

            image = Image(key=s3_key, category=ImageCategoryEnum.services)
            db.add(image)
            await db.flush()  # to get image.id
            image_id = image.id
        except Exception as e:
            image_id = None

        activity = Activity(
            name=name,
            description=description,
            image_id=image_id
        )
        db.add(activity)

        await db.flush()
        print(f"Seeder - Activity: {name}")
        n += 1

    await db.commit()
    print(f"Seeder: Seeded {n} activities")

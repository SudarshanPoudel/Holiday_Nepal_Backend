import json
from pathlib import Path
from app.database.seeder.utils import get_file_path, load_data
from app.modules.activities.graph import ActivityGraphRepository, ActivityNode
from app.utils.helper import slugify
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.modules.activities.models import Activity
from app.modules.storage.models import Image, ImageCategoryEnum
from app.modules.storage.service import StorageService  # Use your actual S3 service import
from app.utils.image_utils import validate_and_process_image

async def seed_default_activities(db: AsyncSession, graph_db: Neo4jSession):
    activities = load_data("files/default_activities.json")
    for activity in activities:
        name = activity["name"]
        slug = slugify(name)
        description = activity.get("description")
        image_path = get_file_path(f"files/images/activities/{activity['image_path']}")
        result = await db.execute(select(Activity).filter_by(name_slug=slug))
        if result.scalar():
            continue

        with open(image_path, "rb") as f:
            content = validate_and_process_image(f.read(), resize_to=(1080, 720))

        s3_key = f"activities/{slug}.webp"
        s3_service = StorageService()
        await s3_service.upload_file(key=s3_key, file_content=content, content_type="image/webp")
        image_url = s3_service.get_file_url(s3_key)

        image = Image(key=s3_key, url=image_url, category=ImageCategoryEnum.services)
        db.add(image)
        await db.flush()  # to get image.id
        activity = Activity(
            name=name,
            name_slug=slug,
            description=description,
            image_id=image.id
        )
        db.add(activity)

        await db.flush()
        activity = ActivityNode(id=activity.id, name=name)
        activity_repo = ActivityGraphRepository(graph_db)
        await activity_repo.create(activity)

    await db.commit()

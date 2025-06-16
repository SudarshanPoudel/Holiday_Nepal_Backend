import json
from pathlib import Path
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.modules.places.models import Place
from app.modules.place_activities.models import PlaceActivity
from app.modules.storage.models import Image, ImageCategoryEnum
from app.modules.address.models import Municipality
from app.modules.activities.models import Activity
from app.modules.storage.service import StorageService 

PLACE_JSON_PATH = "app/seeders/files/data/default_places.json"

async def seed_default_places(db: AsyncSession):
    path = Path(PLACE_JSON_PATH)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    data = json.loads(path.read_text())
    for entry in data:
        # Municipality lookup
        mun = await db.scalar(select(Municipality).where(Municipality.name == entry["municipality"]))
        if not mun:
            print(f"Municipality not found: {entry['municipality']}")
            continue

        # Skip existing place
        existing = await db.scalar(select(Place).where(Place.name == entry["name"], Place.municipality_id == mun.id))
        if existing:
            continue

        place = Place(
            name=entry["name"],
            categories=entry.get("categories"),
            longitude=entry["longitude"],
            latitude=entry["latitude"],
            description=entry.get("description"),
            municipality_id=mun.id
        )
        db.add(place)
        await db.flush()

        # Place images upload
        for img_path in entry.get("images", []):
            p = Path(img_path)
            if not p.exists():
                print(f"Image not found: {p}")
                continue
            key = f"places/{slugify(place.name)}-{p.stem}.webp"
            content = p.read_bytes()
            s3_service = StorageService()
            await s3_service.upload_file(key=key, file_content=content, content_type="image/webp")
            url = s3_service.get_file_url(key)
            img = Image(key=key, url=url, category=ImageCategoryEnum.place)
            db.add(img)
            await db.flush()
            place.images.append(img)

        # Link activities to place
        for act_entry in entry.get("activities", []):
            activity = await db.scalar(select(Activity).where(Activity.name == act_entry["name"]))
            if not activity:
                print(f"Activity not found: {act_entry['name']}")
                continue

            pa = PlaceActivity(
                place_id=place.id,
                activity_id=activity.id,
                description=act_entry.get("description"),
                average_duration=60,  
                average_cost=100.0    
            )
            db.add(pa)

        await db.commit()
    print("Default places seeded.")

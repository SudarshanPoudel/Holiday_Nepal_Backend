import json
from pathlib import Path
from sqlalchemy import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.embeddings import get_embedding
from neo4j import AsyncSession as Neo4jSession
from app.database.seeder.utils import get_file_path, load_data
from app.modules.place_activities.graph import PlaceActivityEdge
from app.modules.places.graph import CityPlaceEdge, PlaceGraphRepository, PlaceNode
from app.modules.places.schema import PlaceCategoryEnum
from app.utils.image_utils import validate_and_process_image
from app.utils.helper import slugify, symmetric_pair

from app.modules.places.models import Place, place_images
from app.modules.place_activities.models import PlaceActivity
from app.modules.storage.models import Image, ImageCategoryEnum
from app.modules.cities.models import City
from app.modules.activities.models import Activity
from app.modules.storage.service import StorageService 


async def seed_default_places(db: AsyncSession, graph_db: Neo4jSession):
    data = load_data("files/default_places.json")
    place_repository = PlaceGraphRepository(graph_db)
    n = 0
    for entry in data:
        # City lookup
        mun = await db.scalar(
            select(City).where(City.name == entry["city"])
        )
        if not mun:
            print(f"City not found: {entry['city']}")
            continue

        # Skip if place already exists
        existing = await db.scalar(
            select(Place).where(
                Place.name == entry["name"], Place.city_id == mun.id
            )
        )
        if existing:
            continue
        
        embedding= get_embedding(entry["description"])

        # Create place
        place = Place(
            name=entry["name"],
            category=PlaceCategoryEnum(entry.get("category")),
            latitude=entry["latitude"],
            longitude=entry["longitude"],
            description=entry.get("description"),
            city_id=mun.id,
            average_visit_duration=entry.get("average_visit_duration"),
            average_visit_cost=entry.get("average_visit_cost"),
            embedding=embedding
        )
        db.add(place)
        await db.flush()  # get place.id

        place_node = PlaceNode(id=place.id, name=entry['name'], category=entry['category'])
        await place_repository.create(place_node)
        city_place = CityPlaceEdge(source_id=mun.id, target_id=place.id)
        await place_repository.add_edge(city_place)
        
        # Upload images to S3 and associate
        images = []
        for img_path in entry.get("images", []):
            p = get_file_path(f"../../../seeder-images/places/{img_path}")
            key = f"places/{slugify(place.name)}.webp"

            # Check if image already exists
            existing_img = await db.scalar(select(Image).where(Image.key == key))
            if existing_img:
                images.append(existing_img)
                continue

            # Upload new image
            try:
                with open(p, "rb") as f:
                    content = f.read()
                content = validate_and_process_image(content, resize_to=(1080, 720))
                s3_service = StorageService()
                await s3_service.upload_file(key=key, file_content=content, content_type="image/webp")
                img = Image(
                    key=key,
                    category=ImageCategoryEnum.place
                )
                db.add(img)
                await db.flush()
                images.append(img)
            except Exception as e:
                print(f"Failed to upload image {p}: {e}")
                continue

        # Link images
        for image in images:
            existing = await db.scalar(
                select(place_images).where(
                    place_images.c.place_id == place.id, place_images.c.image_id == image.id
                )
            )
            if existing:
                continue
            await db.execute(insert(place_images).values(place_id=place.id, image_id=image.id))

        # Link activities
        for act_entry in entry.get("activities", []):
            activity = await db.scalar(select(Activity).where(Activity.name == act_entry["name"]))
            if not activity:
                print(f"Activity not found: {act_entry['name']}")
                continue

            existing = await db.scalar(
                select(PlaceActivity).where(
                    PlaceActivity.place_id == place.id, PlaceActivity.activity_id == activity.id
                )
            )
            if existing:
                continue

            pa = PlaceActivity(
                place_id=place.id,
                activity_id=activity.id,
                title=act_entry.get("title"),
                description=act_entry.get("description"),
                average_duration=act_entry.get("average_duration", 60),
                average_cost=act_entry.get("average_cost", 1000)
            )
            db.add(pa)
            await db.flush()

            edge = PlaceActivityEdge(id=pa.id, source_id=place.id, target_id=activity.id)
            await place_repository.add_edge(edge)

        await db.commit()
        n += 1
        print(f"Seeder - Place: {place.name}")

    print(f"Seeder: Seeded {n} places")
    

from sqlalchemy import select
from app.modules.cities.graph import CityGraphRepository, CityNode
from app.modules.cities.models import City
from app.database.seeder.utils import load_data
from shapely.geometry import Point
from app.modules.places.repository import PlaceRepository
import numpy as np
from geoalchemy2.shape import from_shape

async def seed_default_cities(db, graph_db):
    default_cities = load_data("files/default_cities.json")
    graph_repo = CityGraphRepository(graph_db)
    n = 0
    for city in default_cities:
        existing = await db.execute(
            select(City).where(City.name == city["name"])
        )
        existing_city = existing.scalar_one_or_none()

        if not existing_city:
            lat, lon = city["location"]
            db_city = City(
                name=city["name"],
                latitude=lat,
                longitude=lon,
                location=from_shape(Point(lon, lat), srid=4326)
            )

            db.add(db_city)
            await db.commit()
            await db.refresh(db_city)

            city_node = CityNode(id=db_city.id, name=db_city.name)
            await graph_repo.create(city_node)

            n += 1

        print(f"Seeder - City: {city['name']}")
    print(f"Seeder: Seeded {n} cities")


async def update_city_embeddings(db):
    print("Seeder: Updating city embeddings")
    repo = PlaceRepository(db)
    places = await repo.get_all()

    # Group embeddings by city_id
    city_embeddings = {}
    for place in places:
        if place.embedding is not None:
            city_embeddings.setdefault(place.city_id, []).append(np.array(place.embedding))

    # Fetch all cities
    cities = await db.execute(select(City))
    cities = cities.scalars().all()

    # Update each city's embedding
    for city in cities:
        embeddings = city_embeddings.get(city.id)
        if embeddings:
            avg_embedding = np.mean(embeddings, axis=0)
            city.embedding = avg_embedding.tolist()
        else:
            city.embedding = None

    await db.commit()
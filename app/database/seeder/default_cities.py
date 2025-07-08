from sqlalchemy import select
from app.modules.cities.graph import CityGraphRepository, CityNode
from app.modules.cities.models import City
from app.modules.cities.repository import CityRepository
from app.database.seeder.utils import load_data
from shapely.geometry import Point
from geoalchemy2.shape import from_shape

async def seed_default_cities(db, graph_db):
    city_entered = 0

    default_cities = load_data("files/default_cities.json")
    graph_repo = CityGraphRepository(graph_db)

    for city in default_cities:
        # Use raw query to check by name
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

            city_entered += 1

    print(f"Seeder: Default cities seeded.")

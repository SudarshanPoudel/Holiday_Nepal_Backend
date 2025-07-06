from app.modules.cities.graph import CityGraphRepository, CityNode
from app.modules.cities.schema import CityBase
from app.modules.cities.repository import CityRepository
from app.database.seeder.utils import load_data

async def seed_default_cities(db, graph_db):
    city_entered = 0


    # Create default districts
    default_cities = []
    city_repo = CityRepository(db)
    graph_repo = CityGraphRepository(graph_db)

    default_cities = load_data("files/default_cities.json")

    for city in default_cities:
        existing_city = await city_repo.get_all_filtered(filters={"name": city["name"]})

        if not existing_city:
            city = CityBase(
                name=city["name"], latitude=city['location'][0], longitude=city['location'][1]
            )
            db_city = await city_repo.create(city)
            city_node = CityNode(id=db_city.id, name=city["name"])
            await graph_repo.create(city_node)
            city_entered += 1
                
    print(f"Seeder: Seeded {city_entered} cities.")
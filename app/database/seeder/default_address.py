from app.modules.address.graph import CityGraphRepository, CityNode
from app.modules.address.schema import DistrictBase, CityBase
from app.modules.address.repository import DistrictRepository, CityRepository
from app.database.seeder.utils import load_data

async def seed_default_address(db, graph_db):
    district_entered = 0
    city_entered = 0


    # Create default districts
    default_address = []
    dist_repo = DistrictRepository(db)
    muni_repo = CityRepository(db)
    graph_repo = CityGraphRepository(graph_db)

    default_address = load_data("files/default_address.json")

    for dist in default_address:
        existing_dist = await dist_repo.get_all_filtered(filters={"name": dist["name"]})

        if existing_dist:
            district_id = existing_dist[0].id

        else:
            district = DistrictBase(name=dist["name"], headquarter=dist["headquarter"])
            new_dist = await dist_repo.create(district)
            district_id = new_dist.id
            district_entered += 1

        for muni in dist["cities"]:
            if muni['location'] is None:    
                continue
            existing_muni = await muni_repo.get_all_filtered(filters={"name": muni["name"], "district_id": district_id})

            if not existing_muni:
                city = CityBase(
                    name=muni["name"], district_id=district_id, longitude=muni['location'][1], latitude=muni['location'][0]
                )
                db_city = await muni_repo.create(city)
                city_node = CityNode(id=db_city.id, name=muni["name"])
                await graph_repo.create(city_node)
                city_entered += 1
                
    print(f"Seeder: Seeded {district_entered} districts and {city_entered} cities.")
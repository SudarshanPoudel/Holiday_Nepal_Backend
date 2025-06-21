from app.modules.address.graph import MunicipalityGraphRepository, MunicipalityNode
from app.modules.address.schema import DistrictBase, MunicipalityBase
from app.modules.address.repository import DistrictRepository, MunicipalityRepository
from app.database.seeder.utils import load_data

async def seed_default_address(db, graph_db):
    district_entered = 0
    municipality_entered = 0


    # Create default districts
    default_address = []
    dist_repo = DistrictRepository(db)
    muni_repo = MunicipalityRepository(db)
    graph_repo = MunicipalityGraphRepository(graph_db)

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

        for muni in dist["municipalities"]:
            if muni['location'] is None:    
                continue
            existing_muni = await muni_repo.get_all_filtered(filters={"name": muni["name"], "district_id": district_id})

            if not existing_muni:
                municipality = MunicipalityBase(
                    name=muni["name"], district_id=district_id, longitude=muni['location'][1], latitude=muni['location'][0]
                )
                db_municipality = await muni_repo.create(municipality)
                municipality_node = MunicipalityNode(id=db_municipality.id, name=muni["name"])
                await graph_repo.create(municipality_node)
                municipality_entered += 1
                
    print(f"Seeder: Seeded {district_entered} districts and {municipality_entered} municipalities.")
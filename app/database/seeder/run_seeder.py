from app.database.graph_database import get_graph_db
from app.database.seeder.default_accomodation_service import seed_default_accomodation_services
from app.database.seeder.default_activities import seed_default_activities
from app.database.seeder.default_cities import seed_default_cities
from app.database.seeder.default_bucket import create_bucket_if_not_exists
from app.database.seeder.default_places import seed_default_places
from app.database.database import get_db 
import asyncio

from app.database.seeder.default_transport_routes import seed_default_transport_routes
from app.database.seeder.default_transport_service import seed_default_transport_services
from app.database.seeder.default_users import seed_default_users

async def run_seeder():

    create_bucket_if_not_exists()
    async for db in get_db():
        async for graph_db in get_graph_db():
            await seed_default_cities(db, graph_db)
            await seed_default_users(db)
            await seed_default_activities(db, graph_db)
            await seed_default_places(db, graph_db)
            await seed_default_transport_routes(db, graph_db)
            await seed_default_transport_services(db, graph_db)
            await seed_default_accomodation_services(db)
            
    print("Seeder: Seeding completed.")

if __name__ == "__main__":
    asyncio.run(run_seeder())
    
from seeder.default_address import seed_default_address
from seeder.default_bucket import create_bucket_if_not_exists
from seeder.default_profile_seeder import default_profile_seeder
from app.database.database import get_db 
import asyncio

async def run_seeder():

    create_bucket_if_not_exists()
    await default_profile_seeder()
    async for db in get_db():
        await seed_default_address(db)
        
    print("Seeder: Seeding completed.")

if __name__ == "__main__":
    asyncio.run(run_seeder())
    
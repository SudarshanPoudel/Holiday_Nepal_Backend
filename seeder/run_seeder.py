from seeder.default_bucket import create_bucket_if_not_exists
from seeder.default_profile_seeder import default_profile_seeder
import asyncio

async def run_seeder():
    create_bucket_if_not_exists()
    await default_profile_seeder()

    print("Seeder: Seeding completed.")

if __name__ == "__main__":
    asyncio.run(run_seeder())
    
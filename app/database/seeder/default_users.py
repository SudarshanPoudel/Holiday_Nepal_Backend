import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.all_models import User, City
from app.database.seeder.utils import get_file_path, load_data  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_default_users(db: AsyncSession):
    users_data = load_data("files/default_users.json")
    n = 0
    for user_data in users_data:
        email = user_data["email"]
        username = user_data["username"]
        city_name = user_data["city"]

        # Check if user already exists
        existing_user = await db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing_user.scalar():
            continue

        # Find city ID
        result = await db.execute(
            select(City).where(City.name == city_name)
        )
        city = result.scalar_one_or_none()
        if not city:
            print(f"City '{city_name}' not found, skipping user '{username}'")
            continue

        hashed_password = pwd_context.hash(user_data["password"])

        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
            city_id=city.id
        )

        db.add(new_user)
        n += 1
        print(f"Seeder - User: {username}")

    await db.commit()
    print(f"Seeder: Seeded {n} users")

import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.all_models import User, Municipality
from app.database.seeder.utils import get_file_path, load_data  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_default_users(db: AsyncSession):
    users_data = load_data("files/default_users.json")
    for user_data in users_data:
        email = user_data["email"]
        username = user_data["username"]
        municipality_name = user_data["muicipality"]

        # Check if user already exists
        existing_user = await db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing_user.scalar():
            continue

        # Find municipality ID
        result = await db.execute(
            select(Municipality).where(Municipality.name == municipality_name)
        )
        municipality = result.scalar_one_or_none()
        if not municipality:
            print(f"Municipality '{municipality_name}' not found, skipping user '{username}'")
            continue

        hashed_password = pwd_context.hash(user_data["password"])

        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
            municipality_id=municipality.id
        )

        db.add(new_user)

    await db.commit()
    print("Default users seeded.")

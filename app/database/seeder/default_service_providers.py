import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.all_models import User, ServiceProvider
from app.database.seeder.utils import load_data
from app.modules.service_provider.schema import ServiceProviderCategoryEnum  # adjust import

async def seed_default_service_providers(db: AsyncSession):
    providers_data = load_data("files/default_service_providers.json")

    for provider in providers_data:
        username = provider["username"]

        # Find user by username
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User '{username}' not found. Skipping provider '{provider['name']}'")
            continue

        # Skip if a service provider is already linked to this user
        existing = await db.execute(select(ServiceProvider).where(ServiceProvider.user_id == user.id))
        if existing.scalar():
            continue

        new_provider = ServiceProvider(
            name=provider["name"],
            description=provider["description"],
            contact_no=provider["contact_no"],
            address=provider["address"],
            longitude=provider["longitude"],
            latitude=provider["latitude"],
            category=ServiceProviderCategoryEnum(provider["category"]),
            is_verified=False,
            user_id=user.id
        )

        db.add(new_provider)

    await db.commit()
    print("Default service providers seeded.")

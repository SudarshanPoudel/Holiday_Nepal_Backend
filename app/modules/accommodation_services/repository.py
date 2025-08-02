from sqlite3 import IntegrityError
from typing import List
from fastapi_pagination import Params
from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.accommodation_services.models import AccomodationService, accommodation_service_images
from app.modules.accommodation_services.schema import AccomodationServiceBase, AccomodationServiceFilter

class AccomodationServiceRepository(BaseRepository[AccomodationService, AccomodationServiceBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(AccomodationService, db)

    async def add_images(self, accommodation_service_id: int, image_ids: List[int]):
        values = [{"accommodation_service_id": accommodation_service_id, "image_id": image_id} for image_id in image_ids]
        
        stmt = insert(accommodation_service_images).values(values)
        try:
            await self.db.execute(stmt)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

    async def update_images(self, accommodation_service_id: int, image_ids: List[int]):
        delete_stmt = delete(accommodation_service_images).where(accommodation_service_images.c.accommodation_service_id == accommodation_service_id)
        await self.db.execute(delete_stmt)

        # Add new image mappings
        if image_ids:
            values = [{"accommodation_service_id": accommodation_service_id, "image_id": image_id} for image_id in image_ids]
            await self.db.execute(insert(accommodation_service_images).values(values))

        await self.db.commit()

    async def recommand(self, user_id: int, city_id: int, load_relations: List[str] = []):
        data = await self.index(params = Params(page=1, size=10), filters=AccomodationServiceFilter(city_id=city_id), load_relations=load_relations)
        return data.items
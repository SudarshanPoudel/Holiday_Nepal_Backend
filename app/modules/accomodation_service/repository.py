from sqlite3 import IntegrityError
from typing import List
from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.accomodation_service.models import AccomodationService, accomodation_service_images
from app.modules.accomodation_service.schema import AccomodationServiceCreate

class AccomodationServiceRepository(BaseRepository[AccomodationService, AccomodationServiceCreate]):
    def __init__(self, db):
        super().__init__(AccomodationService, db)

    async def add_images(self, accomodation_service_id: int, image_ids: List[int]):
        values = [{"accomodation_service_id": accomodation_service_id, "image_id": image_id} for image_id in image_ids]
        
        stmt = insert(accomodation_service_images).values(values)
        try:
            await self.db.execute(stmt)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

    async def update_images(self, place_id: int, image_ids: List[int]):
        delete_stmt = delete(accomodation_service_images).where(accomodation_service_images.c.place_id == place_id)
        await self.db.execute(delete_stmt)

        # Add new image mappings
        if image_ids:
            values = [{"place_id": place_id, "image_id": image_id} for image_id in image_ids]
            await self.db.execute(insert(accomodation_service_images).values(values))

        await self.db.commit()
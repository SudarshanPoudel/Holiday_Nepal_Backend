from typing import List
from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.repository import BaseRepository
from app.modules.place_activities.models import PlaceActivity
from app.modules.place_activities.schema import PlaceActivityCreate
from app.modules.places.models import Place, place_images
from app.modules.places.schema import PlaceRead


class PlaceRepository(BaseRepository[Place, PlaceRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Place, db)

    async def add_images(self, place_id: int, image_ids: List[int]):
        values = [{"place_id": place_id, "image_id": image_id} for image_id in image_ids]
        
        stmt = insert(place_images).values(values)
        try:
            await self.db.execute(stmt)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

    async def update_images(self, place_id: int, image_ids: List[int]):
        delete_stmt = delete(place_images).where(place_images.c.place_id == place_id)
        await self.db.execute(delete_stmt)

        # Add new image mappings
        if image_ids:
            values = [{"place_id": place_id, "image_id": image_id} for image_id in image_ids]
            await self.db.execute(insert(place_images).values(values))

        await self.db.commit()

    async def update_activities(self, place_id: int, activities: List[PlaceActivityCreate]):
        delete_stmt = delete(PlaceActivity).where(PlaceActivity.place_id == place_id)
        await self.db.execute(delete_stmt)

        # Add new image mappings
        if activities:
            values = [{"place_id": place_id, **activity.model_dump()} for activity in activities]
            await self.db.execute(insert(PlaceActivity).values(values))

        await self.db.commit()
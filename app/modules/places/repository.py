from typing import Any, List, Optional
from sqlalchemy import insert, delete, select
from sqlalchemy.orm import selectinload , joinedload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.repository import BaseRepository
from app.modules.place_activities.models import PlaceActivity
from app.modules.place_activities.schema import PlaceActivityCreate
from app.modules.places.models import Place, place_images
from app.modules.places.schema import PlaceBase
from app.utils.embeddings import get_embedding


class PlaceRepository(BaseRepository[Place, PlaceBase]):
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

    async def delete_activities(self, place_id: int):
        delete_stmt = delete(PlaceActivity).where(PlaceActivity.place_id == place_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()

    

    async def vector_search(self, query: str, limit: int = 10, load_relations: Optional[List[str]] = None, extra_conditions: Optional[List[Any]] = None) -> List[Place]:
        embedding = get_embedding(query)
        stmt = select(Place).where(Place.embedding != None)
        if load_relations:
            for relation in load_relations:
                if '.' in relation:
                    parts = relation.split('.')
                    current_model = Place
                    option = None
                    for part in parts:
                        attr = getattr(current_model, part)
                        current_model = attr.property.mapper.class_
                        option = joinedload(attr) if option is None else option.joinedload(attr)
                    stmt = stmt.options(option)
                else:
                    stmt = stmt.options(selectinload(getattr(Place, relation)))

        if extra_conditions:
            for condition in extra_conditions:
                stmt = stmt.filter(condition)

        stmt = stmt.order_by(Place.embedding.cosine_distance(embedding)).limit(limit)
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
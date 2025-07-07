from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.places.models import Place
from app.modules.storage.schema import ImageRead

async def get_place_image(db: AsyncSession, place_id: int, single=True):
    stmt = (
        select(Place)
        .options(selectinload(Place.images))
        .where(Place.id == place_id)
    )
    result = await db.execute(stmt)
    place = result.scalar_one_or_none()
    
    if not place or not place.images:
        return None if single else []

    if single:
        return ImageRead.model_validate(place.images[0])
    return [ImageRead.model_validate(image) for image in place.images]

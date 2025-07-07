from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.storage.repository import ImageRepository
from app.modules.storage.schema import ImageRead
from app.modules.transport_service.schema import TransportServiceCategoryEnum


async def get_image_from_transport_service_category(db: AsyncSession, category: TransportServiceCategoryEnum):
    image_repo = ImageRepository(db)
    image = await image_repo.get(1)
    return ImageRead.model_validate(image, from_attributes=True)
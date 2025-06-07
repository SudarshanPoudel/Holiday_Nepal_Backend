from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.storage.models import Image
from app.modules.storage.schema import ImageRead

class ImageRepository(BaseRepository[Image, ImageRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Image, db)
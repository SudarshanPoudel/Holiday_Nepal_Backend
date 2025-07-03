from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.storage.models import Image
from app.modules.storage.schema import ImageRead
from app.modules.storage.service import StorageService

class ImageRepository(BaseRepository[Image, ImageRead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Image, db)

    async def delete(self, id: int):
        storage_service = StorageService()
        image = await self.repository.get(id)
        if not image:
            raise HTTPException(detail="Image not found", status_code=404)
        await self.delete(id)
        await storage_service.delete_file(image.key)
        return True
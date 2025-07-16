from email import message
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from app.core.schemas import BaseResponse
from app.modules.storage.repository import ImageRepository
from app.modules.storage.schema import ImageCreate, ImageCategoryEnum, ImageRead
from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image


class StorageController:
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service
        self.repository = ImageRepository(db)
    
    async def upload_image(self, file: UploadFile, category: ImageCategoryEnum):
        image_bytes = await file.read()
        verified_image = validate_and_process_image(image_bytes)
        key = StorageService.generate_unique_key(file_extension='webp')
        final_key = await self.storage_service.upload_file(
            key=f"{category.value}/{key}",
            file_content= verified_image,
            content_type=file.content_type
        )
        data = ImageCreate(key=final_key, category=category)
        try:
            image = await self.repository.create(data)
        except Exception as e:
            await self.storage_service.delete_file(final_key)
            raise HTTPException(status_code=500, detail=str(e))

        return BaseResponse(message="Image Uploaded Successfully", data=ImageRead.model_validate(image, from_attributes=True))
    
    async def get_image(self, id: int):
        image = await self.repository.get(record_id=id)
        if not image:
            raise HTTPException(detail="Image not found", status_code=404)
        return BaseResponse(message="Image Fetched Successfully", data=ImageRead.model_validate(image, from_attributes=True))
    
    async def update_image(self, id: int, file: UploadFile):
        image = await self.repository.get(id)
        if not image:
            raise HTTPException(detail="Image not found", status_code=404)
        image_bytes = await file.read()
        verified_image = validate_and_process_image(image_bytes)
        await self.storage_service.upload_file(
            key=image.key,
            file_content= verified_image,
            content_type=file.content_type
        )
        return BaseResponse(message="Image Replaced Successfully", data=ImageRead.model_validate(image, from_attributes=True))
    
    async def delete_image(self, id: int):  
        await self.repository.delete(id)
        return BaseResponse(message="Image Deleted Successfully")
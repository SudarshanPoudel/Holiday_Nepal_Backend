from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.modules.storage.service import StorageService


class StorageController:
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service
    
    def upload_image(self, file: UploadFile):
        key = StorageService.generate_unique_key(file_extension=file.filename.split(".")[-1])
        self.storage_service.upload_file(
            key=f"uploads/{key}",
            file_content= file.file.read(),
            content_type=file.content_type
        )
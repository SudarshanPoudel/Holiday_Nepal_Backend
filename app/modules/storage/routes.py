from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.database.database import get_db
from app.modules.storage.controller import StorageController
from app.modules.storage.service import StorageService

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db), storage = Depends(StorageService)):
    try:
        controller = StorageController(db, storage)
        return await controller.upload_image(file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
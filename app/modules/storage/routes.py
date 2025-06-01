from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.database.database import get_db
from app.modules.storage.controller import StorageController
from app.modules.storage.schema import ImageCategoryEnum
from app.modules.storage.service import StorageService

router = APIRouter()

@router.post("/")
async def upload_image(file: UploadFile, category: ImageCategoryEnum, db: AsyncSession = Depends(get_db), storage = Depends(StorageService)):
    try:
        controller = StorageController(db, storage)
        return await controller.upload_image(file, category)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_image(id: int, db: AsyncSession = Depends(get_db), storage = Depends(StorageService)):
    try:
        controller = StorageController(db, storage)
        return await controller.get_image(id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  

@router.put("/")
async def update_image(id: int, file: UploadFile, db: AsyncSession = Depends(get_db), storage = Depends(StorageService)):
    try:
        controller = StorageController(db, storage)
        return await controller.update_image(id, file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/")
async def delete_image(id: int, db: AsyncSession = Depends(get_db), storage = Depends(StorageService)):
    try:
        controller = StorageController(db, storage)
        return await controller.delete_image(id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
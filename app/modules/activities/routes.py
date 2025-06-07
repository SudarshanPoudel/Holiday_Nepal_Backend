from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.controller import ActivityController
from app.modules.activities.schema import ActivityCreate, ActivityUpdate


router = APIRouter()

@router.post("/")
async def create_activity(activity: ActivityCreate, db: AsyncSession = Depends(get_db)):
    try:
        controller = ActivityController(db)
        return await controller.create(activity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_all_activities(db: AsyncSession = Depends(get_db)):
    try:
        controller = ActivityController(db)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{activity_id}")
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = ActivityController(db)
        return await controller.get(activity_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{activity_id}")
async def update_activity(activity: ActivityUpdate, db: AsyncSession = Depends(get_db)):
    try:
        controller = ActivityController(db)
        return await controller.update(activity.id, activity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{activity_id}")
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = ActivityController(db)
        return await controller.delete(activity_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
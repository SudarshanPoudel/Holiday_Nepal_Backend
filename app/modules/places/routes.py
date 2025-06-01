from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.controller import PlaceController
from app.modules.places.schema import CreatePlace, UpdatePlace


router = APIRouter()


@router.post("/")
async def create_place(place: CreatePlace, db: AsyncSession = Depends(get_db)):
    try:
        controller = PlaceController(db)
        return await controller.create(place)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_all_places(db: AsyncSession = Depends(get_db)):
    try:
        controller = PlaceController(db)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{place_id}")
async def get_place(place_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = PlaceController(db)
        return await controller.get(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{place_id}")
async def update_place(place_id: int, place: UpdatePlace, db: AsyncSession = Depends(get_db)):
    try:
        controller = PlaceController(db)
        return await controller.update(place_id, place)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{place_id}")
async def delete_place(place_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = PlaceController(db)
        return await controller.delete(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Depends, HTTPException, Query
from app.modules.cities.controller import CityController
from app.modules.cities.schema import CityCreate
from fastapi_pagination import Params
from typing import Optional
import traceback
from app.database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

@router.post("/")
async def add_city(city: CityCreate, db: AsyncSession = Depends(get_db)):
    controller = CityController(db)
    try:
        return await controller.add_city(city)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_city_by_name(
    search: Optional[str] = Query(None, description="Search query for city name"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        controller = CityController(db)
        return await controller.index(search=search, params=params)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/nearest")
async def get_nearest_cities(
    latitude: float,
    longitude: float,
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db)
):
    controller = CityController(db)
    try:
        return await controller.nearest(latitude=latitude, longitude=longitude, params=params)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{city_id}")
async def update_city(city_id: int, city: CityCreate, db: AsyncSession = Depends(get_db)):
    controller = CityController(db)
    try:
        return await controller.update_city(city_id, city)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{city_id}")
async def delete_city(city_id: int, db: AsyncSession = Depends(get_db)):
    controller = CityController(db)
    try:
        return await controller.delete_city(city_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
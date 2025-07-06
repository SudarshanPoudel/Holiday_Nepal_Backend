from fastapi import APIRouter, Depends, HTTPException
from app.modules.cities.controller import CityController
from fastapi_pagination import Params
from git import Optional
from yarl import Query
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()
    
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
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/nearest")
async def get_nearest_cities(
    lng: float,
    lat: float,
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db)
):
    controller = CityController(db)
    try:
        return await controller.nearest(lng=lng, lat=lat, params=params)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
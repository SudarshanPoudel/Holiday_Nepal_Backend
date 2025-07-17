from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.database.graph_database import get_graph_db
from neo4j import AsyncSession as Neo4jSession
from app.modules.cities.controller import CityController
from app.modules.cities.schema import CityCreate
from fastapi_pagination import Params
from typing import Optional
import traceback
from app.core.role_check import require_admin
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/")
async def add_city(
    city: CityCreate, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    controller = CityController(db, graph_db)
    try:
        return await controller.add_city(city)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def index_city(
    search: Optional[str] = Query(None, description="Search query for city name"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        controller = CityController(db, graph_db)
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
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    controller = CityController(db, graph_db)
    try:
        return await controller.nearest(latitude=latitude, longitude=longitude, params=params)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{city_id}")
async def update_city(
    city_id: int, 
    city: CityCreate, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    controller = CityController(db, graph_db)
    try:
        return await controller.update_city(city_id, city)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{city_id}")
async def delete_city(
    city_id: int, 
    request: Request,
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    controller = CityController(db, graph_db)
    try:
        return await controller.delete_city(city_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.database.graph_database import get_graph_db
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.modules.places.controller import PlaceController
from app.modules.places.schema import CreatePlace, PlaceFilters, UpdatePlace


router = APIRouter()


@router.post("/")
async def create_place(place: CreatePlace, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.create(place)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_places(
    request: Request,
    search: Optional[str] = Query(None, description="Search query for service provider name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    filters: Optional[PlaceFilters] = Depends(PlaceFilters),
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession  =  Depends(get_graph_db)
):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.index(
            params=params,
            search=search,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/all")
async def get_all_places(db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{place_id}")
async def get_place(place_id: int, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.get(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{place_id}")
async def update_place(place_id: int, place: UpdatePlace, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.update(place_id, place)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{place_id}")
async def delete_place(place_id: int, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.delete(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
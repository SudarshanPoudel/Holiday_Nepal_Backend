from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.graph_database import get_graph_db
from fastapi_pagination import Params
import traceback
from app.core.role_check import require_admin
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from app.modules.places.controller import PlaceController
from app.modules.places.schema import PlaceCreate, PlaceFilters

router = APIRouter()

@router.post("/")
async def create_place(
    place: PlaceCreate, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.create(place)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_places(
    search: Optional[str] = Query(None, description="Search query for place name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    filters: Optional[PlaceFilters] = Depends(PlaceFilters),
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
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
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{place_id}")
async def get_place(
    place_id: int, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.get(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{place_id}")
async def update_place(
    place_id: int, 
    place: PlaceCreate, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.update(place_id, place)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{place_id}")
async def delete_place(
    place_id: int, 
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession = Depends(get_graph_db),
    _: None = Depends(require_admin)
):
    try:
        controller = PlaceController(db, graph_db)
        return await controller.delete(place_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
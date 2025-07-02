from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.database.graph_database import get_graph_db
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.modules.activities.controller import ActivityController
from app.modules.activities.schema import ActivityCreate, ActivityUpdate


router = APIRouter()

@router.post("/")
async def create_activity(activity: ActivityCreate, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = ActivityController(db, graph_db)
        return await controller.create(activity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_activities(
    search: Optional[str] = Query(None, description="Search query for service provider name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db), 
    graph_db: Neo4jSession  =  Depends(get_graph_db),
):
    try:
        controller = ActivityController(db, graph_db)
        return await controller.index(
            params=params,
            search=search,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{activity_id}")
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = ActivityController(db, graph_db)
        return await controller.get(activity_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{activity_id}")
async def update_activity(activity: ActivityUpdate, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = ActivityController(db, graph_db)
        return await controller.update(activity.id, activity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{activity_id}")
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db), graph_db: Neo4jSession  =  Depends(get_graph_db)):
    try:
        controller = ActivityController(db, graph_db)
        return await controller.delete(activity_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
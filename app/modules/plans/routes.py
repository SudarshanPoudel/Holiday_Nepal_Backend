from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import traceback
from app.database.database import get_db
from fastapi_pagination import Params

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.redis_cache import RedisCache, get_redis_cache
from neo4j import AsyncSession as Neo4jSession
from app.modules.plans.controller import PlanController
from app.modules.plans.schema import PlanCreate, PlanFilters

router = APIRouter()

@router.post("/")
async def create_plan(
    request: Request, 
    plan: PlanCreate, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.create(plan)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def index_plans(
    request: Request,
    search: Optional[str] = Query(None, description="Search query for plan title"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    filters: Optional[PlanFilters] = Depends(PlanFilters),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
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

@router.get("/{plan_id}")
async def get_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.get(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.delete(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{plan_id}")
async def update_plan(
    plan_id: int, 
    plan: PlanCreate, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.update(plan_id, plan)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/{plan_id}")
async def partial_update_plan(
    plan_id: int, 
    data: Dict, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.partial_update(plan_id, data)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{plan_id}/duplicate")
async def duplicate_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.duplicate(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{plan_id}/undo")
async def undo_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db),
    redis_cache: RedisCache  = Depends(get_redis_cache("plan"))
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.undo(plan_id, redis_cache)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{plan_id}/toggle-save")
async def toggle_save_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.toggle_save(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{plan_id}/rate")
async def rate_plan(
    plan_id: int, 
    rating: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.rate(plan_id, rating)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{plan_id}/rate")
async def delete_rate_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.delete_rate(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Depends, HTTPException, Request
import traceback
from app.database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from app.database.graph_database import get_graph_db
from app.modules.plans.controller import PlanController
from app.modules.plans.schema import PlanCreate

router = APIRouter()

@router.post("/")
async def create_plan(
    request: Request, 
    plan: PlanCreate, 
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, graph_db, user_id)
        return await controller.create(plan)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}")
async def get_plan(
    plan_id: int, 
    request: Request, 
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, graph_db, user_id)
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
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, graph_db, user_id)
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
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, graph_db, user_id)
        return await controller.update(plan_id, plan)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
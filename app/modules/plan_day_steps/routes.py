from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
import traceback
from app.database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from app.database.graph_database import get_graph_db
from app.modules.plan_day_steps.controller import PlanDayStepController
from app.modules.plan_day_steps.schema import PlanDayStepCreate
router = APIRouter()

@router.get("/{plan_day_step_id}/transport-services")
async def get_transport_services_recommendations(
    request: Request,
    plan_day_step_id: int,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.get_transport_services(plan_day_step_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def add_plan_day_step(
    request: Request, 
    plan_step: PlanDayStepCreate,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.add_plan_day_step(plan_step)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plan_day_step_id}")
async def delete_plan_day_step(
    request: Request, 
    plan_day_step_id: int,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.delete_day_step(plan_day_step_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{plan_day_step_id}")
async def reorder_plan_day_step(
    request: Request, 
    plan_day_step_id: int,
    plan_day_id: int,
    next_step_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.reorder_day_step(plan_day_step_id, plan_day_id, next_step_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
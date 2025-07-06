from fastapi import APIRouter, Depends, HTTPException, Request
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession
from app.database.graph_database import get_graph_db
from app.modules.plan_day_steps.controller import PlanDayStepController
from app.modules.plan_day_steps.schema import PlanDayStepCreate
router = APIRouter()

@router.get("/{plan_day_step_id}")
async def get_plan_day_step(
    request: Request, 
    plan_day_step_id: int,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.get(plan_day_step_id)
    except HTTPException as e:
        raise e
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def delete_plan_day(
    request: Request, 
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    graph_db: Neo4jSession = Depends(get_graph_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayStepController(db, graph_db, user_id)
        return await controller.delete_day_step(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.plan_day_steps.schema import PlanDayStepCreate
from app.modules.plans.controller import PlanController
from app.modules.plans.schema import PlanCreate


router = APIRouter()

@router.post("/")
async def create_plan(request: Request, plan: PlanCreate, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.create(plan)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{plan_id}")
async def get_plan(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.get(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.delete(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{plan_id}/add-day")
async def add_day(plan_id: int, title:str, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.add_day(plan_id, title)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{plan_id}/delete-day")
async def delete_day(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.delete_day(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/add-step")
async def add_day_step(plan_id: int, step: PlanDayStepCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.add_day_step(plan_id, step)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{plan_id}/delete-step")
async def delete_day_step(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = PlanController(db, user_id)
        return await controller.delete_day_step(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
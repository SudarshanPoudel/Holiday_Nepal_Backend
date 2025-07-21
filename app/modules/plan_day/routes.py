from fastapi import APIRouter, Depends, HTTPException, Request
import traceback
from app.database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.plan_day.controller import PlanDayController
router = APIRouter()


@router.post("/")
async def add_plan_day(
    request: Request, 
    plan_id: int,
    title: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayController(db, user_id)
        return await controller.add_day(plan_id, title)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{plan_day_id}")
async def update_plan_day(
    request: Request, 
    plan_day_id: int,
    title: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayController(db, user_id)
        return await controller.update(plan_day_id, title)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def delete_plan_day(
    request: Request, 
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayController(db, user_id)
        return await controller.delete_day(plan_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{plan_day_id}/accomodation-services")
async def get_accomodation_services(
    request: Request,
    plan_day_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        controller = PlanDayController(db, user_id)
        return await controller.recommand_accomodation_services(plan_day_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
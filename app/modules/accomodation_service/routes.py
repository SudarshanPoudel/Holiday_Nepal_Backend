from fastapi import APIRouter, Depends, HTTPException, Request
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accomodation_service.controller import AccomodationServiceController
from app.modules.accomodation_service.schema import AccomodationServiceCreate


router = APIRouter()

@router.post("/")
async def create_accomodation_service(accomodation_service: AccomodationServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = AccomodationServiceController(db, user_id)
        return await controller.create(accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_all_accomodation_services(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = AccomodationServiceController(db, user_id)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{accomodation_service_id}")
async def get_accomodation_service(accomodation_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = AccomodationServiceController(db, user_id)
        return await controller.get(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{accomodation_service_id}")
async def update_accomodation_service(accomodation_service_id: int, accomodation_service: AccomodationServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = AccomodationServiceController(db, user_id)
        return await controller.update(accomodation_service_id, accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{accomodation_service_id}")
async def delete_accomodation_service(accomodation_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = AccomodationServiceController(db, user_id)
        return await controller.delete(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
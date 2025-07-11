from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
import traceback
from app.core.role_check import require_admin
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.accomodation_services.controller import AccomodationServiceController
from app.modules.accomodation_services.schema import AccomodationServiceCreate

router = APIRouter()

@router.post("/")
async def create_accomodation_service(
    accomodation_service: AccomodationServiceCreate, 
    db: AsyncSession = Depends(get_db), 
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.create(accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_accomodation_services(
    search: Optional[str] = Query(None, description="Search query for service accomodation name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.index(
            params=params,
            search=search,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{accomodation_service_id}")
async def get_accomodation_service(
    accomodation_service_id: int, 
    db: AsyncSession = Depends(get_db),
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.get(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{accomodation_service_id}")
async def update_accomodation_service(
    accomodation_service_id: int, 
    accomodation_service: AccomodationServiceCreate, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.update(accomodation_service_id, accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{accomodation_service_id}")
async def delete_accomodation_service(
    accomodation_service_id: int, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.delete(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
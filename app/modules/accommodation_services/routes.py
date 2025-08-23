from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
import traceback
from app.core.role_check import require_admin
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.accommodation_services.controller import AccomodationServiceController
from app.modules.accommodation_services.schema import AccomodationServiceCreate

router = APIRouter()

@router.post("/")
async def create_accommodation_service(
    accommodation_service: AccomodationServiceCreate, 
    db: AsyncSession = Depends(get_db), 
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.create(accommodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_accommodation_services(
    search: Optional[str] = Query(None, description="Search query for service accommodation name"),
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

@router.get("/{accommodation_service_id}")
async def get_accommodation_service(
    accommodation_service_id: int, 
    db: AsyncSession = Depends(get_db),
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.get(accommodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{accommodation_service_id}")
async def update_accommodation_service(
    accommodation_service_id: int, 
    accommodation_service: AccomodationServiceCreate, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.update(accommodation_service_id, accommodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{accommodation_service_id}")
async def delete_accommodation_service(
    accommodation_service_id: int, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = AccomodationServiceController(db)
        return await controller.delete(accommodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
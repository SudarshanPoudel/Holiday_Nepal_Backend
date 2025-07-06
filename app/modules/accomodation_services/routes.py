from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accomodation_services.controller import AccomodationServiceController
from app.modules.accomodation_services.schema import AccomodationServiceCreate


router = APIRouter()

@router.post("/")
async def create_accomodation_service(accomodation_service: AccomodationServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = AccomodationServiceController(db)
        return await controller.create(accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def index_accomodation_services(
    request: Request,
    search: Optional[str] = Query(None, description="Search query for service provider name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{accomodation_service_id}")
async def get_accomodation_service(accomodation_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = AccomodationServiceController(db)
        return await controller.get(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{accomodation_service_id}")
async def update_accomodation_service(accomodation_service_id: int, accomodation_service: AccomodationServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = AccomodationServiceController(db)
        return await controller.update(accomodation_service_id, accomodation_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{accomodation_service_id}")
async def delete_accomodation_service(accomodation_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = AccomodationServiceController(db)
        return await controller.delete(accomodation_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transport_service.controller import TransportServiceController
from app.modules.transport_service.schema import TransportServiceCreate, TransportServiceFilters


router = APIRouter()

@router.post("/")
async def create_transport_service(transport_service: TransportServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = TransportServiceController(db, user_id)
        return await controller.create(transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def index_transport_services(
    request: Request,
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    filters: Optional[TransportServiceFilters] = Depends(TransportServiceFilters),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = request.state.user_id
        controller = TransportServiceController(db, user_id)
        return await controller.index(
            params=params,
            sort_by=sort_by,
            order=order,
            filters=filters
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transport_service_id}")
async def get_transport_service(transport_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = TransportServiceController(db, user_id)
        return await controller.get(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{transport_service_id}")
async def update_transport_service(transport_service_id: int, transport_service: TransportServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = TransportServiceController(db, user_id)
        return await controller.update(transport_service_id, transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{transport_service_id}")
async def delete_transport_service(transport_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = request.state.user_id
        controller = TransportServiceController(db, user_id)
        return await controller.delete(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
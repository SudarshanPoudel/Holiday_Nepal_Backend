from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
import traceback
from app.core.role_check import require_admin
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.transport_service.controller import TransportServiceController
from app.modules.transport_service.schema import TransportServiceCreate, TransportServiceFilters

router = APIRouter()

@router.post("/")
async def create_transport_service(
    transport_service: TransportServiceCreate, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = TransportServiceController(db)
        return await controller.create(transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def index_transport_services(
    request: Request,
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    search: Optional[str] = Query(None, description="Search query for transport service description"),
    params: Params = Depends(),
    filters: Optional[TransportServiceFilters] = Depends(TransportServiceFilters),
    db: AsyncSession = Depends(get_db),
):
    try:
        controller = TransportServiceController(db)
        return await controller.index(
            params=params,
            sort_by=sort_by,
            search=search,
            order=order,
            filters=filters
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transport_service_id}")
async def get_transport_service(
    transport_service_id: int, 
    db: AsyncSession = Depends(get_db),
):
    try:
        controller = TransportServiceController(db)
        return await controller.get(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transport_service_id}")
async def update_transport_service(
    transport_service_id: int, 
    transport_service: TransportServiceCreate, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = TransportServiceController(db)
        return await controller.update(transport_service_id, transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{transport_service_id}")
async def delete_transport_service(
    transport_service_id: int, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
):
    try:
        controller = TransportServiceController(db)
        return await controller.delete(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
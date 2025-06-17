from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.service_provider.controller import ServiceProviderController
from app.modules.service_provider.schema import ServiceProviderFilters, ServiceProviderRegister, ServiceProviderUpdate


router = APIRouter()

@router.post("/")
async def register_service_provider(provider: ServiceProviderRegister, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = ServiceProviderController(db, request)
        return await controller.register(provider)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def index_service_providers(
    request: Request,
    search: Optional[str] = Query(None, description="Search query for service provider name"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    filters: Optional[ServiceProviderFilters] = Depends(ServiceProviderFilters),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = request.state.user_id
        controller = ServiceProviderController(db, user_id)
        return await controller.index(
            params=params,
            search=search,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_service_providers(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = ServiceProviderController(db, request)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{provider_id}")
async def get_service_provider(provider_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = ServiceProviderController(db, request)
        return await controller.get(provider_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/")
async def update_service_provider(provider: ServiceProviderUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = ServiceProviderController(db, request)
        return await controller.update(provider)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/")
async def delete_service_provider(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = ServiceProviderController(db, request)
        return await controller.delete()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.service_provider.controller import ServiceProviderController
from app.modules.service_provider.schema import ServiceProviderRegister, ServiceProviderUpdate


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
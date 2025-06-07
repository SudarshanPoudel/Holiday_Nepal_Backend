from fastapi import APIRouter, Depends, HTTPException, Request
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transport_service.controller import TransportServiceController
from app.modules.transport_service.schema import TransportServiceCreate


router = APIRouter()

@router.post("/")
async def create_transport_service(transport_service: TransportServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportServiceController(db, request)
        return await controller.create(transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_all_transport_services(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportServiceController(db, request)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{transport_service_id}")
async def get_transport_service(transport_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportServiceController(db, request)
        return await controller.get(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{transport_service_id}")
async def update_transport_service(transport_service_id: int, transport_service: TransportServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportServiceController(db, request)
        return await controller.update(transport_service_id, transport_service)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{transport_service_id}")
async def delete_transport_service(transport_service_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportServiceController(db, request)
        return await controller.delete(transport_service_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
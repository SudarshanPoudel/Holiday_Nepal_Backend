from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transport_route.controller import TransportRouteController
from app.modules.transport_route.schema import TransportRouteCreate, TransportRouteUpdate


router = APIRouter()

@router.get("/")
async def get_all_transport_routes(db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.get_all()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/")
async def create_transport_route(transport_route: TransportRouteCreate, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.create(transport_route)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/municipality/{municipality_id}")
async def get_transport_routes_by_municipality(municipality_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.get_from_municipality(municipality_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{transport_route_id}")
async def get_transport_route(transport_route_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.get(transport_route_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.put("/{transport_route_id}")
async def update_transport_route(transport_route_id: int, transport_route: TransportRouteUpdate, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.update(transport_route_id, transport_route)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{transport_route_id}")
async def delete_transport_route(transport_route_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = TransportRouteController(db)
        return await controller.delete(transport_route_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
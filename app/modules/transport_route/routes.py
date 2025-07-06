from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.database.graph_database import get_graph_db
from fastapi_pagination import Params
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transport_route.controller import TransportRouteController
from app.modules.transport_route.schema import RouteCategoryEnum, TransportRouteCreate


router = APIRouter()

@router.get("/")
async def index_transport_route(
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
    graph_db = Depends(get_graph_db),
):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.index(
            params=params,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/")
async def create_transport_route(transport_route: TransportRouteCreate, db: AsyncSession = Depends(get_db), graph_db = Depends(get_graph_db)):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.create(transport_route)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/city/{city_id}")
async def get_transport_routes_by_city(city_id: int, route_category:Optional[RouteCategoryEnum] = None, db: AsyncSession = Depends(get_db), graph_db = Depends(get_graph_db)):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.get_from_city(city_id, route_category)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{transport_route_id}")
async def get_transport_route(transport_route_id: int, db: AsyncSession = Depends(get_db), graph_db = Depends(get_graph_db)):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.get(transport_route_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.put("/{transport_route_id}")
async def update_transport_route(transport_route_id: int, transport_route: TransportRouteCreate, db: AsyncSession = Depends(get_db), graph_db = Depends(get_graph_db),):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.update(transport_route_id, transport_route)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{transport_route_id}")
async def delete_transport_route(transport_route_id: int, db: AsyncSession = Depends(get_db), graph_db = Depends(get_graph_db),):
    try:
        controller = TransportRouteController(db, graph_db)
        return await controller.delete(transport_route_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
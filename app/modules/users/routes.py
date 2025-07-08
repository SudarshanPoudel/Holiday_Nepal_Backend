from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
from app.database.database import get_db
from app.modules.users.controller import UserController
from fastapi_pagination import Params
from typing import Optional
from pydantic import BaseModel


router = APIRouter()

@router.get("/")
async def index_users(
    request: Request,
    search: Optional[str] = Query(None, description="Search query for username"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", description="Sorting order: 'asc' or 'desc'"),
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        is_admin = True
        user_controller = UserController(db, is_admin)
        return await user_controller.index(
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
    
@router.get("/{user_id}")
async def get_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        is_admin = True
        controller = UserController(db)
        return await controller.get(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Depends, HTTPException, Request
import traceback
from app.database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.me.controller import MeController


router = APIRouter()

@router.get("/")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user_id = int(request.state.user_id)
        controller = MeController(db, user_id)
        return await controller.me()
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
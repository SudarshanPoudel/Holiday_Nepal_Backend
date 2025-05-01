from app.core.repository import BaseRepository
from app.modules.address.models import District
from fastapi import APIRouter, Depends, HTTPException, Request
from app.modules.auth.controller import AuthController
from app.modules.auth.schemas import UserLogin, UserRegister
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def get_all(db: AsyncSession = Depends(get_db)):
    try:
        repo = BaseRepository(model=District, db=db)
        districts = await repo.get_all()
        return {"districts": districts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    
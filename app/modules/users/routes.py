from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db

router = APIRouter()

router.get("/")
async def get_profile(request: Request, db: AsyncSession = Depends(get_db)):
    return {"message": "Hello, Users!"}
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.repository import PlaceRepository


class RouteService():
    def __init__(self, db: AsyncSession):
        self.db = db

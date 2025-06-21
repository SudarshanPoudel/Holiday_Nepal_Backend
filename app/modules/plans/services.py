from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.repository import PlaceRepository


class PlanService():
    def __init__(self, db: AsyncSession):
        self.db = db

    
    def add_intermediate_route(self, place_id_start:int, place_id_end:int):
        place_repository = PlaceRepository(self.dn)
        place_start = place_repository.get(place_id_start)
        place_end = place_repository.get(place_id_end)
        if not place_start or not place_end:
            raise HTTPException(status_code=404, detail="Place not found")
        
        if place_start.municipality_id == place_end.municipality_id:
            return None
        
        
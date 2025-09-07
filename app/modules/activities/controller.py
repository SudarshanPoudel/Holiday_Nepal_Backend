from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.activities.repository import ActivityRepository
from app.modules.activities.schema import ActivityCreate, ActivityRead, ActivityReadFull

class ActivityController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ActivityRepository(db)
    
    async def create(self, activity: ActivityCreate):
        activity_db = await self.repository.create(activity)
        return BaseResponse(message="Activity created successfully", data={"id": activity_db.id, **activity.model_dump()})   
    
    async def get(self, activity_id: int):
        activity = await self.repository.get(activity_id, load_relations=["image"])
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Activity fetched successfully", data=ActivityReadFull.model_validate(activity, from_attributes=True))

    async def update(self, activity_id: int, activity: ActivityCreate):
        activity_db = await self.repository.update(activity_id, activity)
        if not activity_db:
            raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Activity updated successfully", data={"id": activity_db.id, **activity.model_dump()})

    async def delete(self, activity_id: int):
        delete = await self.repository.delete(activity_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Activity deleted successfully")

    async def index(
        self,
        params: Params,
        search: Optional[str] = None,
        sort_by: Optional[str] = "id",
        order: Optional[str] = "asc",
    ):
        data = await self.repository.index(
            params=params,
            search_fields=["name"],
            search_query=search,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["image"]
        )
        return BaseResponse(message="Activities fetched successfully", data=[ActivityRead.model_validate(ts, from_attributes=True) for ts in data.items])


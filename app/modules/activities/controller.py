from typing import Dict, Optional
from fastapi import HTTPException
from app.modules.activities.graph import ActivityGraphRepository, ActivityNode
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.activities.repository import ActivityRepository
from app.modules.activities.schema import ActivityCreateInternal, ActivityCreate, ActivityRead, ActivityUpdate, ActivityUpdateInternal
from app.modules.storage.service import StorageService
from app.utils.helper import slugify
from app.utils.image_utils import validate_and_process_image


class ActivityController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = ActivityRepository(db)
        self.graph_repository = ActivityGraphRepository(graph_db)
        self.storage_service = StorageService()
    
    async def create(self, activity: ActivityCreate):
        slug = slugify(activity.name)
        existing_activity = await self.repository.get_all_filtered(filters={"name_slug": slug})
        if existing_activity:
            raise HTTPException(status_code=400, detail="Activity with this name already exists")
        
        activity_internal = ActivityCreateInternal(**activity.model_dump(), name_slug=slug)
        activity_db = await self.repository.create(activity_internal)
        await self.graph_repository.create(ActivityNode(id=activity_db.id, name=activity.name))
        return BaseResponse(message="Activity created successfully", data={"id": activity_db.id})   
    
    async def get(self, activity_id: int):
        activity = await self.repository.get(activity_id, load_relations=["image"])
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Activity fetched successfully", data=ActivityRead.model_validate(activity, from_attributes=True))

    async def update(self, activity_id: int, activity: ActivityUpdate):
        name_slug = slugify(activity.name)
        old_activity = await self.repository.get_all_filtered(filters={"name_slug": name_slug})
        if old_activity and old_activity[0].id != activity_id:
            raise HTTPException(status_code=404, detail="Activity with this name already exists")
        activity = ActivityUpdateInternal(**activity.model_dump(), name_slug=name_slug)
        activity = await self.repository.update(activity_id, activity)
        await self.graph_repository.update(activity_id, {"name": activity.name})
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Activity updated successfully", data={"id": activity.id})
    

    async def delete(self, activity_id: int):
        delete = await self.repository.delete(activity_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Activity not found")
        await self.graph_repository.delete(activity_id)
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
        return BaseResponse(message="Transport services fetched successfully", data=[ActivityRead.model_validate(ts, from_attributes=True) for ts in data.items])


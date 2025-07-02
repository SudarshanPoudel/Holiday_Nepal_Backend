from typing import Dict, Optional
from fastapi import HTTPException
from app.modules.place_activities.graph import PlaceActivityEdge, PlaceActivityGraphRepository
from app.modules.places.graph import PlaceGraphRepository, PlaceNode
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from neo4j import AsyncSession as Neo4jSession
from app.modules.activities.schema import ActivityCreateInternal
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.place_activities.schema import PlaceActivityCreateInternal, PlaceActivityUpdateInternal
from app.modules.places.repository import PlaceRepository
from app.modules.places.schema import CreatePlace, CreatePlaceInternal, PlaceRead, UpdatePlace, UpdatePlaceInternal
from app.utils.helper import slugify, symmetric_pair
from app.utils.image_utils import validate_and_process_image


class PlaceController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = PlaceRepository(db)
        self.graph_repository = PlaceGraphRepository(graph_db)
        self.place_activity_repository = PlaceActivityRepository(db)
        self.place_activity_graph_repository = PlaceActivityGraphRepository(graph_db)

    async def create(self, place: CreatePlace):
        slug = slugify(place.name)

        place_db = CreatePlaceInternal(**place.model_dump(exclude={"activities", "image_ids"}), name_slug=slug)
        place_db = await self.repository.create(place_db)
        await self.graph_repository.create(PlaceNode(id=place_db.id, name=place.name, category=place.category))
        await self.repository.add_images(place_db.id, place.image_ids)
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityCreateInternal(place_id=place_db.id, **activity.model_dump())
                place_activity = await self.place_activity_repository.create(place_acitivity)
                await self.place_activity_graph_repository.create(PlaceActivityEdge(start_id=place_db.id, end_id=place_activity.activity_id))
            except:
                raise HTTPException(status_code=404, detail="Activity not found")

        return BaseResponse(message="Place created successfully", data={"id": place_db.id})
    
    
    async def get(self, place_id: int):
        place = await self.repository.get(place_id, load_relations=["images", "place_activities.activity.image", "municipality"])
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return BaseResponse(message="Place fetched successfully", data=PlaceRead.from_model(place))
    
    async def get_all(self):
        res = await self.repository.get_all(load_relations=["images", "place_activities.activity.image", "municipality"])
        return BaseResponse(message="Places fetched successfully", data=[PlaceRead.from_model(p) for p in res])

    async def delete(self, place_id: int):
        delete = await self.repository.delete(place_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Place not found")
        await self.graph_repository.delete(place_id)
        return BaseResponse(message="Place deleted successfully")
    

    async def update(self, place_id: int, place:UpdatePlace):
        place_internal = UpdatePlaceInternal(**place.model_dump(exclude={"activities", "image_ids"}))
        place_db = await self.repository.update(place_id, place_internal)
        if not place_db:
            raise HTTPException(status_code=404, detail="Place not found")
        await self.graph_repository.update(place_id, {"name": place.name, "category": place.category})
        await self.repository.update_images(place_id, place.image_ids)
        await self.place_activity_repository.clear_place_activities(place_id)
        await self.place_activity_graph_repository.clear_edges(place_id, edge_type=PlaceActivityEdge)
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityUpdateInternal(place_id=place.id, **activity.model_dump())
                await self.place_activity_repository.update(activity.id, place_acitivity)
                await self.place_activity_graph_repository.update(symmetric_pair(place_id, activity.id), {"end_id": activity.activity_id})
            except:
                raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Place updated successfully", data={"id": place_db.id})
    
    async def index(
        self,
        params: Params,
        search: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None,
        sort_by: Optional[str] = "id",
        order: Optional[str] = "asc",
    ):
        data = await self.repository.index(
            params=params,
            filters=filters,
            search_fields=["name"],
            search_query=search,
            sort_field=sort_by,
            sort_order=order,
            load_relations=["images", "place_activities.activity.image", "municipality"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[PlaceRead.model_validate(ts, from_attributes=True) for ts in data.items])

from typing import Dict, Optional
from fastapi import HTTPException
from app.modules.place_activities.graph import PlaceActivityEdge
from app.modules.places.graph import CityPlaceEdge, PlaceGraphRepository, PlaceNode
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from neo4j import AsyncSession as Neo4jSession
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.place_activities.schema import PlaceActivityBase
from app.modules.places.repository import PlaceRepository
from app.modules.places.schema import PlaceCreate, PlaceBase, PlaceRead

class PlaceController():
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession):
        self.db = db
        self.graph_db = graph_db
        self.repository = PlaceRepository(db)
        self.graph_repository = PlaceGraphRepository(graph_db)
        self.place_activity_repository = PlaceActivityRepository(db)

    async def create(self, place: PlaceCreate):
        place_db = await self.repository.create(PlaceBase(**place.model_dump(exclude={"activities", "image_ids"})))
        await self.graph_repository.create(PlaceNode(id=place_db.id, name=place.name, category=place.category))
        await self.graph_repository.add_edge(CityPlaceEdge(source_id=place.city_id, target_id=place_db.id))
        await self.repository.add_images(place_db.id, place.image_ids)
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityBase(place_id=place_db.id, **activity.model_dump())
                place_activity_db = await self.place_activity_repository.create(place_acitivity)
                await self.graph_repository.add_edge(PlaceActivityEdge(id=place_activity_db.id, source_id=place_db.id, target_id=place_activity_db.activity_id))
            except Exception as e:
                print(e)
                raise HTTPException(status_code=404, detail="Activity not found")

        place_info = await self.repository.get(place_db.id, load_relations=["images", "place_activities.activity.image", "city"])
        return BaseResponse(message="Place created successfully", data=PlaceRead.model_validate(place_info))
    
    async def get(self, place_id: int):
        place = await self.repository.get(place_id, load_relations=["images", "place_activities.activity.image", "city"])
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return BaseResponse(message="Place fetched successfully", data=PlaceRead.model_validate(place))
    
    async def delete(self, place_id: int):
        delete = await self.repository.delete(place_id)
        if not delete:
            raise HTTPException(status_code=404, detail="Place not found")
        await self.graph_repository.delete(place_id)
        return BaseResponse(message="Place deleted successfully")
    

    async def update(self, place_id: int, place:PlaceCreate):
        place_internal = PlaceBase(**place.model_dump(exclude={"activities", "image_ids"}))
        place_db = await self.repository.update(place_id, place_internal)
        if not place_db:
            raise HTTPException(status_code=404, detail="Place not found")
        await self.repository.update_images(place_id, place.image_ids)
        await self.repository.delete_activities(place_id)
        await self.graph_repository.update(PlaceNode(id=place_id, name=place.name, category=place.category))
        await self.graph_repository.clear_edges(place_id, edge_type=PlaceActivityEdge)
        await self.graph_repository.clear_edges(place_id, edge_type=CityPlaceEdge)
        await self.graph_repository.add_edge(CityPlaceEdge(source_id=place.city_id, target_id=place_id))
        for activity in place.activities:
            place_activity = PlaceActivityBase(place_id=place_id, **activity.model_dump())
            place_activity = await self.place_activity_repository.create(place_activity)
            await self.graph_repository.add_edge(PlaceActivityEdge(id=place_activity.id, source_id=place_id, target_id=activity.activity_id))
        place = await self.repository.get(place_id, load_relations=["images", "place_activities.activity.image", "city"])
        return BaseResponse(message="Place updated successfully", data=PlaceRead.model_validate(place))
    
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
            load_relations=["images", "place_activities.activity.image", "city"]
        )
        return BaseResponse(message="Transport services fetched successfully", data=[PlaceRead.model_validate(ts) for ts in data.items])

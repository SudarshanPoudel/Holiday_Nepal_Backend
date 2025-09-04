from typing import Dict, Optional
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.modules.place_activities.schema import PlaceActivityBase
from app.modules.places.repository import PlaceRepository
from app.modules.places.schema import PlaceCreate, PlaceBase, PlaceRead

class PlaceController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PlaceRepository(db)

    async def create(self, place: PlaceCreate):
        place_db = await self.repository.create(PlaceBase(**place.model_dump(exclude={"activities", "image_ids"})))
        await self.repository.add_images(place_db.id, place.image_ids)
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityBase(place_id=place_db.id, **activity.model_dump())
                await self.place_activity_repository.create(place_acitivity)
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
        return BaseResponse(message="Place deleted successfully")
    

    async def update(self, place_id: int, place:PlaceCreate):
        place_internal = PlaceBase(**place.model_dump(exclude={"activities", "image_ids"}))
        place_db = await self.repository.update(place_id, place_internal)
        if not place_db:
            raise HTTPException(status_code=404, detail="Place not found")
        await self.repository.update_images(place_id, place.image_ids)
        await self.repository.delete_activities(place_id)
        for activity in place.activities:
            place_activity = PlaceActivityBase(place_id=place_id, **activity.model_dump())
            place_activity = await self.place_activity_repository.create(place_activity)
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

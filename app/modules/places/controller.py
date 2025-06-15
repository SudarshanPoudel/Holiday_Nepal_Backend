import time
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.schemas import BaseResponse
from app.modules.activities.schema import ActivityCreateInternal
from app.modules.place_activities.repository import PlaceActivityRepository
from app.modules.place_activities.schema import PlaceActivityCreateInternal, PlaceActivityUpdateInternal
from app.modules.places.repository import PlaceRepository
from app.modules.places.schema import CreatePlace, CreatePlaceInternal, PlaceRead, UpdatePlace, UpdatePlaceInternal
from app.utils.helper import slugify
from app.utils.image_utils import validate_and_process_image


class PlaceController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PlaceRepository(db)
        self.place_activity_repository = PlaceActivityRepository(db)

    async def create(self, place: CreatePlace):
        slug = slugify(place.name)

        place_db = CreatePlaceInternal(**place.model_dump(exclude={"activities", "image_ids"}), name_slug=slug)
        place_db = await self.repository.create(place_db)

        await self.repository.add_images(place_db.id, place.image_ids)
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityCreateInternal(place_id=place_db.id, **activity.model_dump())
                place_activity = await self.place_activity_repository.create(place_acitivity)
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
        return BaseResponse(message="Place deleted successfully")
    

    async def update(self, place_id: int, place:UpdatePlace):
        place_internal = UpdatePlaceInternal(**place.model_dump(exclude={"activities", "image_ids"}))
        place_db = await self.repository.update(place_id, place_internal)
        if not place_db:
            raise HTTPException(status_code=404, detail="Place not found")
        
        self.repository.update_images(place_id, place.image_ids)
        
        for activity in place.activities:
            try:
                place_acitivity = PlaceActivityUpdateInternal(place_id=place.id, **activity.model_dump())
                await self.place_activity_repository.update(activity.id, place_acitivity)
            except:
                raise HTTPException(status_code=404, detail="Activity not found")
        return BaseResponse(message="Place updated successfully", data={"id": place_db.id})
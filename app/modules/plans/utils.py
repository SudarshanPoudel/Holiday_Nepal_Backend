

from app.modules.plan_day_steps.schema import PlanDayTimeFrameEnum
from app.modules.storage.repository import ImageRepository

# TODO: Implement these utils

class PlanUtils():
    def __init__(self, db):
        self.db = db
        self.image_repository = ImageRepository(db)


    async def get_step_time_frame(self) -> PlanDayTimeFrameEnum:
        return PlanDayTimeFrameEnum.morning 
    
    async def get_step_duration(self) -> float:
        return 3.0
    
    async def get_step_image(self)->int:
        images = await self.image_repository.get_all()
        return images[0].id
    
    async def get_curret_municipality_id(self) -> int:
        return 1
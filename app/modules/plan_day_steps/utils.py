

from app.modules.plan_day.models import PlanDay
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate, PlanDayTimeFrameEnum
from app.modules.plans.models import Plan
from app.modules.storage.repository import ImageRepository

# TODO: Implement these utils

class PlanDayStepUtils():
    def __init__(self, db):
        self.db = db
        self.image_repository = ImageRepository(db)

    async def get_step_time_frame(self, day: PlanDay, step_duration: float) -> PlanDayTimeFrameEnum:
        starting_hour = sum(step.duration for step in day.steps) / 60
        ending_hour = starting_hour + (step_duration / 60)
        duration = ending_hour - starting_hour

        # full day if long or spans multiple time ranges
        if duration >= 6 or (starting_hour < 5 <= ending_hour) or (starting_hour < 12 <= ending_hour) or \
        (starting_hour < 17 <= ending_hour) or (starting_hour < 21 <= ending_hour):
            return PlanDayTimeFrameEnum.full_day

        if 5 <= starting_hour < 12:
            return PlanDayTimeFrameEnum.morning
        elif 12 <= starting_hour < 17:
            return PlanDayTimeFrameEnum.afternoon
        elif 17 <= starting_hour < 21:
            return PlanDayTimeFrameEnum.evening
        else:
            return PlanDayTimeFrameEnum.night

    
    async def get_step_duration(self, step) -> float:
        return 4.0
    
    async def get_step_cost(self) -> float:
        return 1000
    
    async def get_step_image(self)->int:
        images = await self.image_repository.get_all()
        return images[0].id
    
    async def get_curret_city_id(self, plan: Plan) -> int:
        for plan_day in reversed(plan.days):
            for step in reversed(plan_day.steps):
                if step.end_city_id:
                    return step.end_city_id

        return plan.start_city_id

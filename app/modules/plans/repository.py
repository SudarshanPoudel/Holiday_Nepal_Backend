from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload , joinedload

from app.core.repository import BaseRepository
from app.modules.plans.models import Plan
from app.modules.plans.schema import PlanBase, PlanRead

class PlanRepository(BaseRepository[Plan, PlanBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plan, db)
        
    
    async def get_updated_plan(self, plan_id: int, calculate_cost: bool = False) -> Optional[PlanRead]:
        load_relations = [
            "start_city",
            "days.steps.place",
            "days.steps.place_activity.activity.image",
            "days.steps.city_start",
            "days.steps.city_end",
            "days.steps.image",
            "days.steps.route_hops.route.start_city",
            "days.steps.route_hops.route.end_city",
            "user.image"
        ]
        self.db.expire_all()
        query = select(self.model).filter_by(id=plan_id)

        for relation in load_relations:
            parts = relation.split(".")
            current_model = self.model
            option = None

            for i, part in enumerate(parts):
                attr = getattr(current_model, part)
                current_model = attr.property.mapper.class_
                if i == 0:
                    option = selectinload(attr)
                else:
                    option = option.joinedload(attr)

            query = query.options(option)

        result = await self.db.execute(query)
        plan = result.unique().scalar_one_or_none()

        if not plan:
            return None
        
        plan_data = PlanRead.model_validate(plan, from_attributes=True)
    
        cost = 0
        for day in plan_data.days:
            for step in day.steps:
                step.cost = step.cost * self._find_cost_multiplier(plan.no_of_people)
                cost += step.cost
        plan_data.estimated_cost = cost
        await self.update_from_dict(plan_id, {"estimated_cost": cost})
        return plan_data


    def _find_cost_multiplier(self, no_of_people: int) -> float:
        if no_of_people <= 0:
            raise ValueError("No of people must be greater than 0")
        if no_of_people == 1:
            return 1.0
        elif no_of_people<=5:
            return no_of_people * 0.85
        elif no_of_people<=10:
            return no_of_people * 0.75
        elif no_of_people <= 20:
            return no_of_people * 0.65
        else:
            return no_of_people * 0.5
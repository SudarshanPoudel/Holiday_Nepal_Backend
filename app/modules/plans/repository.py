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
        
    
    async def get_updated_plan(self, plan_id: int) -> Optional[PlanRead]:
        load_relations = [
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
            if '.' in relation:
                parts = relation.split('.')
                current_model = self.model
                option = None
                for part in parts:
                    attr = getattr(current_model, part)
                    current_model = attr.property.mapper.class_
                    option = joinedload(attr) if option is None else option.joinedload(attr)
                query = query.options(option)
            else:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.db.execute(query)
        plan = result.unique().scalar_one_or_none()

        if not plan:
            return None
        return PlanRead.model_validate(plan, from_attributes=True)

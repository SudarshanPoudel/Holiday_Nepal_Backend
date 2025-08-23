from sqlalchemy import and_, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day.models import PlanDay


class PlanDayRepository(BaseRepository[PlanDay, PlanDayCreate]):
    def __init__(self, db):
        super().__init__(PlanDay, db)

    async def create(self, plan_day: PlanDayCreate):
        new_day = PlanDay(**plan_day.model_dump())
        self.db.add(new_day)
        await self.db.flush()
        print(new_day.next_plan_day_id)
            
        if new_day.next_plan_day_id:
            res = await self.db.execute(select(PlanDay).where(
                and_(
                    PlanDay.next_plan_day_id == new_day.next_plan_day_id,
                    not_(PlanDay.id == new_day.id)
                )
            ))
        else:
            res = await self.db.execute(select(PlanDay).where(
                and_(
                    PlanDay.plan_id == new_day.plan_id,
                    PlanDay.next_plan_day_id.is_(None),
                    not_(PlanDay.id == new_day.id)
                )
            ))

        prev = res.scalar_one_or_none()
        print(prev)

        if prev:
            await self.db.execute(update(PlanDay).where(PlanDay.id == prev.id).values(next_plan_day_id=new_day.id))


        await self.db.commit()
        await self.db.refresh(new_day)
        return new_day
    
    async def delete(self, plan_day_id: int):
        plan_day = await super().get(plan_day_id)
        if not plan_day:
            return False

        await self.db.execute(update(PlanDay).where(PlanDay.next_plan_day_id == plan_day.id).values(next_plan_day_id=plan_day.next_plan_day_id))
            
        await self.db.delete(plan_day)
        await self.db.commit()
        return True


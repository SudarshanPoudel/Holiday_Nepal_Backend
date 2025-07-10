from typing import Optional
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload , joinedload

from app.core.repository import BaseRepository
from app.modules.plan_day.models import PlanDay
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.plan_route_hops.models import PlanRouteHop
from app.modules.plans.models import Plan, UserPlanRating, user_saved_plans
from app.modules.plans.schema import PlanBase, PlanRead

class PlanRepository(BaseRepository[Plan, PlanBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plan, db)
   
    async def duplicate_plan(self, plan_id: int, new_user_id: int) -> Plan:
        original_plan = await self.get(
            plan_id,
            load_relations=[
                "days.steps.route_hops",
            ],
        )
        if not original_plan:
            return None

        # Create new plan instance
        new_plan = Plan(
            user_id=new_user_id,
            title=original_plan.title + " (Copy)",
            description=original_plan.description,
            no_of_days=original_plan.no_of_days,
            no_of_people=original_plan.no_of_people,
            estimated_cost=original_plan.estimated_cost,
            is_private=True,
            image_id=original_plan.image_id,
            start_city_id=original_plan.start_city_id,
        )

        new_plan.days = []
        for old_day in original_plan.days:
            new_day = PlanDay(
                index=old_day.index,
                title=old_day.title,
                plan=new_plan  # Set parent relationship (plan_id will be auto set)
            )

            new_day.steps = []
            for old_step in old_day.steps:
                new_step = PlanDayStep(
                    index=old_step.index,
                    title=old_step.title,
                    category=old_step.category,
                    time_frame=old_step.time_frame,
                    duration=old_step.duration,
                    cost=old_step.cost,
                    image_id=old_step.image_id,
                    place_id=old_step.place_id,
                    place_activity_id=old_step.place_activity_id,
                    start_city_id=old_step.start_city_id,
                    end_city_id=old_step.end_city_id,
                    plan_day=new_day  # Set parent relationship (plan_day_id auto)
                )

                # Clone route hops
                new_step.route_hops = [
                    PlanRouteHop(
                        route_id=hop.route_id,
                        index=hop.index,
                        destination_city_id=hop.destination_city_id,
                        plan_day_step=new_step  # Set parent (plan_day_step_id auto)
                    )
                    for hop in old_step.route_hops
                ]

                new_day.steps.append(new_step)

            new_plan.days.append(new_day)

        self.db.add(new_plan)
        await self.db.flush()  # Flush assigns IDs and persists relationships
        return new_plan

    
    async def rate_plan(self, user_id: int, plan_id: int, rating: int) -> bool:
        existing_rating_value = await self.get_rating(user_id, plan_id)
        plan = await self.get(plan_id)
        if plan.is_private:
            return False

        if existing_rating_value is not None:
            total_rating = plan.rating * plan.vote_count
            total_rating = total_rating - existing_rating_value + rating
            plan.rating = round(total_rating / plan.vote_count, 2)

            stmt = select(UserPlanRating).where(
                UserPlanRating.user_id == user_id,
                UserPlanRating.plan_id == plan_id
            )
            result = await self.db.execute(stmt)
            existing_rating = result.scalar_one()
            existing_rating.rating = rating
        else:
            total_rating = (plan.rating or 0) * (plan.vote_count or 0)
            total_rating += rating
            plan.vote_count = (plan.vote_count or 0) + 1
            plan.rating = round(total_rating / plan.vote_count, 2)

            new_rating = UserPlanRating(user_id=user_id, plan_id=plan_id, rating=rating)
            self.db.add(new_rating)

        await self.db.commit()
        return True
    
    async def remove_plan_rating(self, user_id: int, plan_id: int) -> bool:
        existing_rating_value = await self.get_rating(user_id, plan_id)
        if existing_rating_value is None:
            return False

        stmt = select(UserPlanRating).where(
            UserPlanRating.user_id == user_id,
            UserPlanRating.plan_id == plan_id
        )
        result = await self.db.execute(stmt)
        rating_row = result.scalar_one()

        plan = await self.get(plan_id)

        if plan.vote_count and plan.vote_count > 1:
            total_rating = plan.rating * plan.vote_count
            total_rating -= existing_rating_value
            plan.vote_count -= 1
            plan.rating = round(total_rating / plan.vote_count, 2)
        else:
            plan.vote_count = 0
            plan.rating = None

        await self.db.delete(rating_row)
        await self.db.commit()
        return True
        
    async def toggle_save_plan(self, user_id: int, plan_id: int) -> bool:
        """
        Toggles save/unsave. Returns True if saved, False if unsaved.
        """
        if self.is_saved(user_id, plan_id):
            delete_stmt = delete(user_saved_plans).where(
                user_saved_plans.c.user_id == user_id,
                user_saved_plans.c.plan_id == plan_id
            )
            await self.db.execute(delete_stmt)
            await self.db.commit()
            return False
        else:
            insert_stmt = insert(user_saved_plans).values(
                user_id=user_id, plan_id=plan_id
            )
            await self.db.execute(insert_stmt)
            await self.db.commit()
            return True

    async def is_saved(self, user_id: int, plan_id: int) -> bool:
        stmt = select(user_saved_plans).where(
            user_saved_plans.c.user_id == user_id,
            user_saved_plans.c.plan_id == plan_id
        )
        result = await self.db.execute(stmt)
        return result.first() is not None

    async def get_rating(self, user_id: int, plan_id: int) -> Optional[int]:
        stmt = select(UserPlanRating.rating).where(
            UserPlanRating.user_id == user_id,
            UserPlanRating.plan_id == plan_id
        )
        result = await self.db.execute(stmt)
        rating = result.scalar_one_or_none()
        return rating

    
    
    async def get_updated_plan(self, plan_id: int, user_id: int) -> Optional[PlanRead]:
        load_relations = [
            "image",
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
        plan_data.self_rating = await self.get_rating(user_id, plan_id)
        plan_data.is_saved = await self.is_saved(user_id, plan_id)
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
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy import delete, insert, select, or_, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload , joinedload
from sqlalchemy.orm import joinedload, selectinload
from app.modules.plans.models import user_saved_plans, Plan
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Params, Page
from app.modules.accommodation_services.repository import AccomodationServiceRepository
from app.core.repository import BaseRepository
from app.modules.plan_day.models import PlanDay
from app.modules.plan_day_steps.models import PlanDayStep
from app.modules.plan_route_hops.models import PlanRouteHop
from app.modules.plans.models import Plan, UserPlanRating, user_saved_plans
from app.modules.plans.schema import PlanBase, PlanRead
from app.modules.users.repository import UserRepository

class PlanRepository(BaseRepository[Plan, PlanBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plan, db)
        self.user_repository = UserRepository(self.db)

    async def duplicate_plan(self, plan_id: int, new_user_id: int) -> Plan:
        original_plan = await self.get(plan_id, load_relations=["unordered_days.unordered_steps.route_hops"])
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
        
        new_plan.unordered_days = []
        prev_day = None
        prev_step = None

        for old_day in original_plan.days:
            new_day = PlanDay(
                title=old_day.title,
                plan=new_plan 
            )
            
            if prev_day:
                prev_day.next_plan_day = new_day
            
            new_day.unordered_steps = []
            
            for old_step in old_day.steps:
                new_step = PlanDayStep(
                    title=old_step.title,
                    category=old_step.category,
                    duration=old_step.duration,
                    cost=old_step.cost,
                    image_id=old_step.image_id,
                    place_id=old_step.place_id,
                    place_activity_id=old_step.place_activity_id,
                    city_id=old_step.city_id,
                    plan_day=new_day  
                )
                
                if prev_step:
                    prev_step.next_plan_day_step = new_step
                
                new_step.route_hops = [
                    PlanRouteHop(
                        route_id=hop.route_id,
                        index=hop.index,
                        destination_city_id=hop.destination_city_id,
                        plan_day_step=new_step  
                    )
                    for hop in old_step.route_hops
                ]
                
                new_day.unordered_steps.append(new_step)
                prev_step = new_step
            
            new_plan.unordered_days.append(new_day)
            prev_day = new_day
        
        self.db.add(new_plan)
        await self.db.flush()  
        return new_plan

    
    async def rate_plan(self, user_id: int, plan_id: int, rating: int) -> Optional[float]:
        existing_rating_value = await self.get_rating(user_id, plan_id)
        plan = await self.get(plan_id)
        if plan.is_private:
            return None

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
        return round(total_rating / plan.vote_count, 2)
    
    async def remove_plan_rating(self, user_id: int, plan_id: int) -> Optional[float]:
        existing_rating_value = await self.get_rating(user_id, plan_id)
        if existing_rating_value is None:
            return None

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
            total_rating = 0

        await self.db.delete(rating_row)
        await self.db.commit()
        if plan.vote_count == 0:
            return 0
        return round(total_rating / plan.vote_count, 2)
        
    async def toggle_save_plan(self, user_id: int, plan_id: int) -> bool:
        """
        Toggles save/unsave. Returns True if saved, False if unsaved.
        """
        if await self.is_saved(user_id, plan_id):
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
        from app.modules.plan_day_steps.service import PlanDayStepService # To avoid circular import

        load_relations = [
            "image",
            "start_city",
            "unordered_days.unordered_steps.place",
            "unordered_days.unordered_steps.place_activity.activity.image",
            "unordered_days.unordered_steps.city",
            "unordered_days.unordered_steps.image",
            "unordered_days.unordered_steps.next_plan_day_step",
            "unordered_days.unordered_steps.route_hops.route.start_city",
            "unordered_days.unordered_steps.route_hops.route.end_city",
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
        
        cost = 0

        plan_data = PlanRead.model_validate(plan, from_attributes=True)
        plan_data.self_rating = await self.get_rating(user_id, plan_id)
        plan_data.is_saved = await self.is_saved(user_id, plan_id)
        
        step_index = 0

        accomodation_repo = AccomodationServiceRepository(self.db)
        last_city_id = plan.start_city_id
        
        for day in plan_data.days:
            day_can_delete = True
            for step in day.steps:
                step.can_delete = await PlanDayStepService._can_delete_step(self.db, step.id)
                step.cost = step.cost * self._find_cost_multiplier(plan.no_of_people)
                last_city_id = step.city.id
                cost += step.cost
                if not step.can_delete:
                    day_can_delete = False
                step.index = step_index
                
                step_index += 1
                if step.route_hops:
                    step.route = await PlanDayStepService.build_simplified_route(step.route_hops)
                    step.route_hops = None
            day.can_delete = day_can_delete
            city_accomodation_cost = await accomodation_repo.get_city_average(last_city_id)
            cost += city_accomodation_cost * self._find_cost_multiplier(plan.no_of_people) 

        n_days = len(plan_data.days)
        image_id = plan_data.image.id if plan_data.image else None
        if not image_id and len(plan_data.days) > 0:
            for day in plan_data.days:
                for step in day.steps:
                    if step.category == "visit" and step.image:
                        plan_data.image = step.image
                        image_id = step.image.id
                        break
                day.can_delete = day_can_delete
                if plan_data.image:
                    break


        self.db.expunge(plan)
        await self.update_from_dict(plan_id, {"estimated_cost": cost, "no_of_days": n_days, "image_id": image_id})
        plan_data.estimated_cost = cost
        plan_data.no_of_days = n_days
        return plan_data


    def _find_cost_multiplier(self, no_of_people: int) -> float:
        if no_of_people <= 0:
            return 0.0
        if no_of_people == 1:
            return 1.0
        elif no_of_people<=5:
            return no_of_people * 0.9
        elif no_of_people<=10:
            return no_of_people * 0.8
        elif no_of_people <= 20:
            return no_of_people * 0.7
        else:
            return no_of_people * 0.6
        

    async def index_saved_plans(
        self,
        user_id: int,
        params: Params,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[list[str]] = None,
        search_query: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: str = "desc",
        load_relations: list[str] = None,
        extra_conditions: Optional[List[Any]] = None
    ) -> Page[Plan]:
        query = (
            select(self.model)
            .join(user_saved_plans, user_saved_plans.c.plan_id == self.model.id)
            .where(user_saved_plans.c.user_id == user_id)
        )

        # apply filters
        if filters:
            for field, value in filters:
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        # apply search
        if search_query and search_fields:
            search_conditions = [
                getattr(self.model, field).ilike(f"%{search_query}%")
                for field in search_fields
                if hasattr(self.model, field)
            ]
            if search_conditions:
                query = query.filter(or_(*search_conditions))

        # apply sorting
        if sort_field and hasattr(self.model, sort_field):
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.order_by(order_func(getattr(self.model, sort_field)))
        else:
            query = query.order_by(desc(self.model.id))

        # load relations
        if load_relations:
            for relation in load_relations:
                if "." in relation:  # nested relation
                    parts = relation.split(".")
                    current_model = self.model
                    option = None
                    for part in parts:
                        attr = getattr(current_model, part)
                        current_model = attr.property.mapper.class_
                        option = joinedload(attr) if option is None else option.joinedload(attr)
                    query = query.options(option)
                else:
                    query = query.options(selectinload(getattr(self.model, relation)))

        # extra conditions
        if extra_conditions:
            for condition in extra_conditions:
                query = query.filter(condition)

        return await paginate(self.db, query, params)

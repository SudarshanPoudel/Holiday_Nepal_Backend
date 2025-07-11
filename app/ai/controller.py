import random
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.core.schemas import BaseResponse
from app.modules.plan_day.graph import PlanDayGraphRepository, PlanDayNode
from app.modules.plan_day.repository import PlanDayRepository
from app.modules.plan_day.schema import PlanDayCreate
from app.modules.plan_day_steps.schema import PlanDayStepCategoryEnum, PlanDayStepCreate
from app.modules.plan_day_steps.service import PlanDayStepService
from app.modules.plans.graph import PlanCityEdge, PlanGraphRepository, PlanNode
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schema import PlanBase


class AIController:
    def __init__(self, db: AsyncSession, graph_db: Neo4jSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.plan_repository = PlanRepository(db)
        self.plan_graph_repository = PlanGraphRepository(graph_db)
        self.plan_day_repository = PlanDayRepository(db)
        self.plan_day_step_service = PlanDayStepService(db, graph_db)
    
    async def generate_plan(self, prompt: str, retry_remaining: int = 10):
        plan_id = None
        try:
            # Randomized metadata
            start_city_id = random.randint(1, 5)
            no_of_people = random.randint(1, 5)
            num_days = random.randint(2, 3)
            current_place = random.randint(1, 3)  # initial place between 1-3

            plan_base = PlanBase(
                title=f"Trip to City {start_city_id}",
                description=f"A trip generated based on your idea: '{prompt}'. Let's explore!",
                user_id=self.user_id,
                is_private=False,
                start_city_id=start_city_id,
                no_of_people=no_of_people,
                image_id=None
            )

            # Create plan
            plan = await self.plan_repository.create(plan_base)
            plan_id = plan.id

            for day_index in range(num_days):
                # Create one day at a time
                await self.plan_day_repository.create(
                    PlanDayCreate(
                        plan_id=plan.id,
                        index=day_index,
                        title=f"Day {day_index + 1}: Exploring Around"
                    )
                )

                # Load plan after adding each day
                await self.db.refresh(plan)
                plan = await self.plan_repository.get(plan.id, load_relations=["days.steps.route_hops"])

                # Add steps for this newly created day
                num_steps = random.randint(1, 2)
                for _ in range(num_steps):
                    category = random.choice([PlanDayStepCategoryEnum.visit, PlanDayStepCategoryEnum.activity])
                    if category == PlanDayStepCategoryEnum.visit:
                        current_place = min(current_place + random.randint(0, 2), 10)
                        step = PlanDayStepCreate(
                            plan_id=plan.id,
                            category=category,
                            place_id=current_place
                        )
                    else:
                        step = PlanDayStepCreate(
                            plan_id=plan.id,
                            category=category,
                            place_activity_id=random.randint(1, 3)
                        )
                  
                    await self.plan_day_step_service.add_step_to_plan(plan=plan, step=step, insert_in_graph=False)

            # Finalize graph creation
            await self.plan_graph_repository.create_from_sql_model(plan, self.user_id, self.db)

            plan_data = await self.plan_repository.get_updated_plan(plan.id, user_id=self.user_id)
            return BaseResponse(message="Random AI-generated plan created", data=plan_data)

        except Exception as e:
            if retry_remaining > 0:
                if plan_id:
                    await self.plan_repository.delete(plan_id)
                return await self.generate_plan(prompt, retry_remaining - 1)
            else:
                raise e
            

    async def edit_plan(self, plan_id: int, prompt: str):
        # Fetch existing plan
        plan = await self.plan_repository.get(plan_id, load_relations=["days.steps.route_hops"])
        if not plan:
            return BaseResponse(message="Plan not found", data=None)

        # Update plan title and description based on prompt
        plan_title = f"AI updated it: {plan.title}"
        plan_description = f"AI updated it: {plan.description}. Based on your idea: '{prompt}'"
        await self.plan_repository.update_from_dict(plan_id, {"title": plan_title, "description": plan_description})
        data = await self.plan_repository.get_updated_plan(plan_id, user_id=self.user_id)
        return BaseResponse(message="Plan updated successfully", data=data)

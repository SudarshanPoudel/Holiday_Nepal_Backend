from pprint import pprint
from typing import AsyncIterator, List, Dict, Any
from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.llm import LLM
from app.modules.ai.agent.prompts import get_prompt, PLAN_JSON_GENERATION_PROMPT, PLAN_OVERVIEW_GENERATION_PROMPT, CITY_ITINERARY_PROMPT
from app.modules.ai.agent.schema import AgentOverallTrip, AgentOverallTripItineraryItem, AgentPlanDay, AgentRetrievedPlace
from app.modules.ai.agent.utils import combine_user_pref_and_prompt_json
from app.modules.cities.models import City
from app.modules.cities.repository import CityRepository
from app.modules.places.models import Place
from app.modules.places.repository import PlaceRepository
from app.modules.users.repository import UserRepository

class TripPlannerAgent:
    def __init__(self, db: AsyncSession):  
        self.db = db
        self.city_repository = CityRepository(db)
        self.place_repository = PlaceRepository(db)

  
    async def generate_overall_plan(self, prompt:str, user_id: int)-> AsyncIterator[AgentOverallTrip]:
        prompt = get_prompt(PLAN_JSON_GENERATION_PROMPT, user_prompt=prompt)
        prompt_dict = await LLM.get_structured_response(prompt)

        user_repo = UserRepository(self.db)
        user_info = await user_repo.get(record_id=user_id, load_relations=["prefer_activities","city"])
        user_pref_dict = { 
            "places": [c.value for c in user_info.prefer_place_categories],
            "activties": [act.name for act in user_info.prefer_activities],
            "distance": user_info.prefer_travel_distance,
            "city": user_info.city.name if user_info.city else None,
            "additional_preferences": user_info.additional_preferences
        }

        final_user_preference = combine_user_pref_and_prompt_json(user_pref_dict, prompt_dict, False, True)

        candidate_cities = await self.city_repository.vector_search(
            query=prompt,
            limit=10
        )
        candidate_city_names = [c.name for c in candidate_cities]
        prompt += f". Plan should start at {final_user_preference.get('start_city')} and end at {final_user_preference.get('end_city')}"

        generation_prompt = get_prompt(PLAN_OVERVIEW_GENERATION_PROMPT, user_prompt=prompt, prompt_metadata=prompt_dict, user_preferences=final_user_preference, candidate_cities=candidate_city_names)
        async for r in LLM.get_structured_stream(generation_prompt, schema=AgentOverallTrip):
            r.start_city = final_user_preference.get('start_city')
            yield r


    async def generate_single_city_plan(self, itinerary: AgentOverallTripItineraryItem, no_of_days: int) -> AsyncIterator[List[AgentPlanDay]]:
        similar_cities = await self.city_repository.get_similar(itinerary.city, limit=1)
        city_id = similar_cities[0].id if similar_cities else None
        relevent_places = await self.place_repository.vector_search(
            query=itinerary.description,
            extra_conditions=[
                Place.city_id == city_id
            ],
            limit=(no_of_days  * 5),
            load_relations=["place_activities.activity"]
        )
        place_items = [AgentRetrievedPlace.model_validate(place) for place in relevent_places]
        retrieved_places = []
        for item in place_items:
            for a in item.place_activities:
                a.name = a.activity.name
                a.activity = None

        retrieved_places = [a.model_dump(exclude_unset=True) for a in place_items]
        iter_dict = {
            "arrival": itinerary.arrival.model_dump() if itinerary.arrival else None,
            "departure": itinerary.departure.model_dump() if itinerary.departure else None,
            "budget": itinerary.budget,
            "description": itinerary.description
        }
        prompt = get_prompt(CITY_ITINERARY_PROMPT, city=itinerary.city, places=retrieved_places, itinerary=iter_dict)

        async for r in LLM.get_structured_stream(prompt, AgentPlanDay):
            yield r
        
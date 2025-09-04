from typing import List, Literal, Optional
from pydantic import BaseModel

from app.modules.places.schema import PlaceCategoryEnum

class AgentOverallTripItineraryArrivalDeparture(BaseModel):
    day: int
    time: str

class AgentOverallTripItineraryItem(BaseModel):
    city: str
    arrival: Optional[AgentOverallTripItineraryArrivalDeparture] = None
    departure: Optional[AgentOverallTripItineraryArrivalDeparture] = None
    travel_around: Optional[bool] = True
    budget: Optional[int] = None
    description: str


class AgentOverallTrip(BaseModel):
    title: str
    description: str
    start_city: Optional[str] = None
    itinerary: List[AgentOverallTripItineraryItem]

class AgentPlanDayStep(BaseModel):
    category: Literal['visit', 'activity']
    place: str
    activity: Optional[str] = None

class AgentPlanDay(BaseModel):
    day: int
    title: str
    steps: List[AgentPlanDayStep]

class AgentRetrievedActivity(BaseModel):
    name: str

    class Config:
        from_attributes = True

class AgentRetrievedPlaceActivity(BaseModel):
    name: Optional[str] = None
    title: str
    description: Optional[str]
    average_duration: Optional[float]
    average_cost: Optional[float]
    activity: AgentRetrievedActivity

    class Config:
        from_attributes = True

class AgentRetrievedPlace(BaseModel):
    name: str
    description: str
    category: PlaceCategoryEnum
    average_visit_duration: float
    average_visit_cost: float
    place_activities: List[AgentRetrievedPlaceActivity]

    class Config:
        from_attributes = True
from typing import List, Optional, Tuple, Union
from pydantic import BaseModel


class AgentImprovedPromptBase(BaseModel):
    refined_prompt: str
    no_of_people: int
    start_city: str

class AgentOverallPlanDayBase(BaseModel):
    title: str
    description: str
    cities: List[str]

class AgentOverallPlanBase(BaseModel):
    title: str
    description: str
    days: List[AgentOverallPlanDayBase]


class AgentPlanDayStepBase(BaseModel):
    category: str
    place: Optional[str] = None
    place_activity: Optional[Tuple[Union[str, None], Union[str, None]]] = None
    end_city: Optional[str] = None


class AgentPlanDayBase(BaseModel):
    title: str
    steps: List[AgentPlanDayStepBase]


class AgentPlanBase(BaseModel):
    title: str
    description: str
    days: List[AgentPlanDayBase]

class AgentEditDataSearchBase(BaseModel):
    query: Optional[str] = None
    top_n: Optional[int] = 0
    cities: Optional[List[str]]

class AgentEditResponseBase(BaseModel):
    response: str
    plan: dict
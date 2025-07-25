from typing import List, Literal, Optional, Tuple, Union
from pydantic import BaseModel


class AgentImprovedPromptBase(BaseModel):
    refined_prompt: str
    no_of_people: Optional[int] = 1
    start_city: str

class AgentOverallPlanDayBase(BaseModel):
    title: str
    description: str
    cities: List[str]

class AgentOverallPlanBase(BaseModel):
    title: str
    description: str
    days: List[AgentOverallPlanDayBase]


class AgentAlreadyDoneTaskBase(BaseModel):
    category: Literal["visit", "activity", "transport", "start_from"]
    name: str
    id: int

class AgentPlanDayStepBase(BaseModel):
    category: Literal["visit", "activity", "transport"]
    place: Optional[str] = None
    place_activity: Optional[Tuple[Union[str, None], Union[str, None]]] = None
    city: Optional[str] = None


class AgentPlanDayBase(BaseModel):
    title: str
    steps: List[AgentPlanDayStepBase]


class AgentPlanBase(BaseModel):
    title: str
    description: str
    days: List[AgentPlanDayBase]

class AgentToAddBase(BaseModel):
    day_index: int
    steps_description: str

class AgentEditDayTitleBase(BaseModel):
    day_index: int
    new_title: str

class AgentMetaChangeBase(BaseModel):
    new_title: Optional[str] = None
    new_description: Optional[str] = None
    new_no_of_people: Optional[int] = None
    new_start_city: Optional[str] = None
    

class AgentSimpleEditRequestBase(BaseModel):
    to_remove: Optional[List[int]] = None
    to_reorder: Optional[List[Tuple[int, int]]] = None
    to_add: Optional[List[AgentToAddBase]] = None
    day_title_change: Optional[List[AgentEditDayTitleBase]] = None
    meta_change: Optional[AgentMetaChangeBase] = None

class AgentEditType(BaseModel):
    type: Literal["simple", "complex", "unrelated"]
    response: Optional[str] = None

class AgentEditPromptRefine(BaseModel):
    type: Literal["simple", "complex", "unrelated"]
    edit: Union[AgentSimpleEditRequestBase, AgentImprovedPromptBase]
    response: Optional[str] = None


class NaturalResponseBase(BaseModel):
    response: str
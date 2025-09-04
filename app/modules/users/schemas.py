from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, model_validator
from typing import List, Optional

from app.modules.cities.schema import CityRead
from app.modules.places.schema import PlaceCategoryEnum
from app.modules.storage.schema import ImageRead

class DistancePreferenceEnum(Enum):
    short = "short"
    medium = "medium"
    long = "long"

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserPlanRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_cost: Optional[float]
    no_of_days: int
    no_of_people: int
    rating: Optional[float]
    vote_count: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    image: Optional[ImageRead] 
    start_city: CityRead

class UserPlanRatingRead(BaseModel):
    rating: int
    plan: UserPlanRead

class UserReadMinimal(BaseModel):
    id: int
    username: str
    city_id: Optional[int] = None

    image: Optional[ImageRead] = None
    
    class Config:
        from_attributes = True

class UserIndex(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr]
    no_of_plans: Optional[int] = None
    
    city: Optional[CityRead] = None
    image: Optional[ImageRead] = None

    class Config:
        from_attributes = True

class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr]
    no_of_plans: Optional[int] = None
    created_at: datetime
    
    city: Optional[CityRead] = None
    image: Optional[ImageRead] = None
    plans: List[UserPlanRead]


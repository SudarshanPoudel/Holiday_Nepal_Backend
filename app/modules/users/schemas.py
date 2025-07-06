from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional

from app.modules.storage.schema import ImageRead

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    city_id: Optional[int]

# Schema for reading user data
class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    image_id: Optional[int] = None
    city_id: Optional[int] = None

    class Config:
        from_attributes = True

# Schema for updating user data
class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    password: Optional[str]
    username: Optional[str]

    city_id: Optional[int]

    class Config:
        from_attributes = True

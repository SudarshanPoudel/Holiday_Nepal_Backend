from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    district_id: Optional[int]
    municipality_id: Optional[int]
    ward_id: Optional[int]

    @model_validator(mode="before")
    def hash_password(cls, values):
        password = values.get("password")
        if password:
            values["password"] = pwd_context.hash(password)
        return values

# Schema for reading user data
class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_verified: bool
    district_id: Optional[int]
    municipality_id: Optional[int]
    ward_id: Optional[int]
    created: datetime

    class Config:
        from_attributes = True

# Schema for updating user data
class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    password: Optional[str]
    username: Optional[str]
    is_verified: Optional[bool]
    district_id: Optional[int]
    municipality_id: Optional[int]
    ward_id: Optional[int]

    @model_validator(mode="before")
    def hash_password(cls, values):
        password = values.get("password")
        if password:
            values["password"] = pwd_context.hash(password)
        return values

    class Config:
        from_attributes = True

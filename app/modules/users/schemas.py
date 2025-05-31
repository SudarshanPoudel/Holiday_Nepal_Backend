from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional

from app.modules.address.schema import MunicipalityBase, DistrictBase

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    municipality_id: Optional[int]

# Schema for reading user data
class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    profile_picture_key: Optional[str] = None
    municipality_id: Optional[int] = None

    class Config:
        from_attributes = True

# Schema for updating user data
class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    password: Optional[str]
    username: Optional[str]

    municipality_id: Optional[int]

    @model_validator(mode="before")
    def hash_password(cls, values):
        password = values.get("password")
        if password:
            values["password"] = pwd_context.hash(password)
        return values

    class Config:
        from_attributes = True

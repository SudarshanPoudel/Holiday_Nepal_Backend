from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    district_id: Optional[int] = None
    municipality_id: Optional[int] = None
    ward_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    district_id: Optional[int] = None
    municipality_id: Optional[int] = None
    ward_id: Optional[int] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
    class Config:
        from_attributes = True


class OTPResponse(BaseModel):
    result: bool
    message: Optional[str] = None

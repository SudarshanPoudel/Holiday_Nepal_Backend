from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    email_or_username: str
    password: str

class Token(BaseModel):
    role: str
    access_token: str
    token_type: str
    user_id: int

class OTPResponse(BaseModel):
    result: bool
    message: Optional[str] = None

from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    email_or_username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class OTPResponse(BaseModel):
    result: bool
    message: Optional[str] = None

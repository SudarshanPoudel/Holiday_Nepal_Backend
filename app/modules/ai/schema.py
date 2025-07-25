from typing import Optional
from pydantic import BaseModel


class AIChat(BaseModel):
    sender: str
    message: str
    index: Optional[int] = None
from pydantic import BaseModel
from typing import Any, Optional

class BaseResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    status_code: int = 200
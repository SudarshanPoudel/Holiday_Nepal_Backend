from pydantic import BaseModel
from typing import Any, Optional

class BaseResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    page: Optional[int] = None
    size: Optional[int] = None
    total: Optional[int] = None
    status_code: int = 200
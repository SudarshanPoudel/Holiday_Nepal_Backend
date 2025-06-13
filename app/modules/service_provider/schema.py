from typing import Optional
from pydantic import BaseModel
from enum import Enum

class ServiceProviderCategoryEnum(Enum):
    ACCOMMODATION = 'accommodation'
    TRANSPORT = 'transport'

class ServiceProviderRegister(BaseModel):
    name: str
    category: ServiceProviderCategoryEnum
    contact_no : str
    address: str
    longitude: float
    latitude: float
    description: Optional[str]

class ServiceProviderUpdate(BaseModel):
    name: Optional[str] 
    category: Optional[ServiceProviderCategoryEnum]
    contact_no: Optional[str]
    address: Optional[str]
    description: Optional[str] 

class ServiceProviderRegisterInternal(ServiceProviderRegister):
    user_id: int

class ServiceProviderUpdateInternal(ServiceProviderUpdate):
    user_id: int

class ServiceProviderRead(BaseModel):
    id: int
    name: str
    is_verified: bool
    user_id: int
    category: ServiceProviderCategoryEnum
    contact_no: str
    address: str
    description: Optional[str]
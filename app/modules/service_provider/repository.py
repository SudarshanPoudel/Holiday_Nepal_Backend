from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.service_provider.models import ServiceProvider
from app.modules.service_provider.schema import ServiceProviderRegister

class ServiceProviderRepository(BaseRepository[ServiceProvider, ServiceProviderRegister]):
    def __init__(self, db: AsyncSession):
        super().__init__(ServiceProvider, db)

    async def get_id_by_user_id(self, user_id: int) -> Optional[ServiceProvider]:
        res = await self.get_by_fields({"user_id": user_id})
        if not res:
            return None
        return res.id
    
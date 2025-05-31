from app.core.repository import BaseRepository
from app.modules.address.models import District, Municipality
from app.modules.address.schema import DistrictBase, MunicipalityBase
from sqlalchemy.ext.asyncio import AsyncSession

class DistrictRepository(BaseRepository[District, DistrictBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=District, db=db)

class MunicipalityRepository(BaseRepository[Municipality, MunicipalityBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Municipality, db=db)
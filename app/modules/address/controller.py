from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Params

from app.core.schemas import BaseResponse
from app.modules.address.repository import DistrictRepository, MunicipalityRepository
from app.modules.address.schema import DistrictBase, MunicipalityBase



class AddressController():
    def __init__(self, db: AsyncSession):
        self.db = db
        self.district_repo = DistrictRepository(db)
        self.municipality_repo = MunicipalityRepository(db)

    async def get_all_district(self):
        res = await self.district_repo.index(params=Params(size=100, page=1), sort_field="name", sort_order="asc")
        return BaseResponse(message="Districts fetched successfully", data=[DistrictBase.model_validate(d, from_attributes=True) for d in res.items])
    
    async def get_all_municipality(self):
        res = await self.municipality_repo.get_all()
        return BaseResponse(message="Municipalities fetched successfully", data=[MunicipalityBase.model_validate(m, from_attributes=True) for m in res])

    async def get_municipality_by_district(self, district_id):
        res = await self.municipality_repo.index(
            params=Params(size=100, page=1),
            sort_field="name",
            filters=[("district_id", district_id)],
            sort_order="asc"
        )
        if not res:
            raise HTTPException(status_code=404, detail="Municipalities not found")
        return BaseResponse(message="Municipalities fetched successfully", data=[MunicipalityBase.model_validate(m, from_attributes=True) for m in res.items])
        
    async def search(self, search: str):
        res = await self.municipality_repo.index(
            params=Params(size=100, page=1),
            search_fields=["name"],
            search_query=search,
        )
        if not res:
            raise HTTPException(status_code=404, detail="Municipalities not found")
        return BaseResponse(message="Municipalities fetched successfully", data=[MunicipalityBase.model_validate(m, from_attributes=True) for m in res.items])
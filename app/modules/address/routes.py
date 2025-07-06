from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.address.controller import AddressController

router = APIRouter()

@router.get("/district")
async def get_all_district(db: AsyncSession = Depends(get_db)):
    try:
        controller = AddressController(db)
        return await controller.get_all_district()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/municipality")
async def get_all_municipality(db: AsyncSession = Depends(get_db)):
    try:
        controller = AddressController(db)
        return await controller.get_all_municipality()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/municiality/search")
async def get_municipality_by_name(name: str, db: AsyncSession = Depends(get_db)):
    try:
        controller = AddressController(db)
        return await controller.search(name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/municipality/{district_id}")
async def get_municipality_by_district(district_id: int, db: AsyncSession = Depends(get_db)):
    try:
        controller = AddressController(db)
        return await controller.get_municipality_by_district(district_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
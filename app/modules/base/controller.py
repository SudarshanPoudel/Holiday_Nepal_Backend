from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


class Controller():
    def __init__(self, db: AsyncSession):
        self.db = db

    
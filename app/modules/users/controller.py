from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request


class UserController:
    def __init__(self,  db: AsyncSession ):
        self.db = db
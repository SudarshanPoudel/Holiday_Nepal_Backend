from app.core.repository import BaseRepository
from app.modules.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.schemas import UserRead


class UserRepository(BaseRepository[User, UserRead]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

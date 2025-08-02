from typing import List, Literal, Optional
from app.database.redis_cache import RedisCache
from app.modules.ai.schema import AIChat

class AICache:
    def __init__(self, redis: RedisCache):
        self.cache = redis
        self.expiry = 60 * 60 * 24 * 30  

    async def push(self, user_id: int, plan_id: int, chat: AIChat):
        session_id = f"{user_id}:{plan_id}"
        existing = await self.get(user_id, plan_id)

        if not existing:
            chat.index = 0
            await self.cache.set(key=session_id, value=[chat.model_dump()], ex=self.expiry)
        else:
            chat.index = len(existing)
            existing.append(chat)
            await self.cache.set(
                key=session_id,
                value=[v.model_dump() for v in existing],
                ex=self.expiry
            )

    async def get(self, user_id: int, plan_id: int) -> List[AIChat] | None:
        vals = await self.cache.get(key=f"{user_id}:{plan_id}", reset_ttl=True)
        if vals:
            chats = [AIChat(**v) for v in vals]
            return sorted(chats, key=lambda x: x.index)
        return None

    async def get_history(self, user_id: int, plan_id: int) -> str:
        chats = await self.get(user_id, plan_id)
        if not chats:
            return ""

        last_chats = chats[-5:]

        lines = []
        for chat in last_chats:
            lines.append(f"{chat.sender}: {chat.message.strip()}")
        return "\n".join(lines)
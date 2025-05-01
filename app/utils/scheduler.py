from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.database.database import SessionLocal
from app.modules.auth.models import RefreshToken
from datetime import datetime

scheduler = AsyncIOScheduler()

async def cleanup_expired_refresh_tokens():
    async with SessionLocal() as session:
        await session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < datetime.utcnow())
        )
        await session.commit()
        print("Expired refresh tokens cleaned up.")

def start_scheduler():
    scheduler.add_job(cleanup_expired_refresh_tokens, 'interval', days=7)
    scheduler.start()

import random
from typing import Union
from app.core.config import settings
import redis.asyncio as redis
from datetime import datetime, timedelta, timezone
import json

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
from app.modules.auth.schemas import OTPResponse



class OTPService:
    OTP_TTL_SECONDS = 300   # OTP valid for 5 mins
    MAX_RESENDS = 5    # Can ask for maximum of 5 resend 
    MAX_MISTAKES = 5    # Can make maximum of 5 mistakes/otp
    RESEND_COOLDOWN = 60    # can ask to resend after 60 sec.ss
    MAX_LIFESPAN = 1800     # Data in redis is delated after 30 sec no matter what

    @staticmethod
    def _otp_key(email): return f"otp:{email}"
    @staticmethod
    def _data_key(email): return f"data:{email}"
    @staticmethod
    def _resend_key(email): return f"resend_count:{email}"
    @staticmethod
    def _first_seen_key(email): return f"first_seen:{email}"
    @staticmethod
    def _last_resend_key(email): return f"last_resend:{email}"
    @staticmethod
    def _otp_attempts_key(email): return f"otp_attempts:{email}"


    @staticmethod
    def generate_otp(): return f"{random.randint(100000, 999999)}"

    async def store_data_and_otp(self, email, data_dict):
        otp = self.generate_otp()
        now = datetime.now(timezone.utc).isoformat()

        await r.set(self._otp_key(email), otp, ex=self.OTP_TTL_SECONDS)
        await r.set(self._data_key(email), json.dumps(data_dict), ex=self.MAX_LIFESPAN)
        await r.set(self._resend_key(email), 0, ex=self.MAX_LIFESPAN)
        await r.set(self._first_seen_key(email), now, ex=self.MAX_LIFESPAN)
        await r.set(self._last_resend_key(email), now, ex=self.RESEND_COOLDOWN)
        return otp


    async def get_data(self, email: str):
        data = await r.get(self._data_key(email))
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None


    async def verify_otp(self, email: str, otp: str) -> OTPResponse:
        real_otp = await r.get(self._otp_key(email))
        if not real_otp:
            return OTPResponse(result=False, message="No active OTP found. Please request a new one.")

        attempts_key = self._otp_attempts_key(email)
        attempts = await r.get(attempts_key)
        if attempts and int(attempts) >= 5:
            return OTPResponse(result=False, message="You have entered the wrong OTP too many times. Please request a new one.")

        if real_otp == otp:
            await r.delete(attempts_key)
            return OTPResponse(result=True, message="OTP verified successfully.")

        await r.incr(attempts_key)
        await r.expire(attempts_key, self.OTP_TTL_SECONDS)
        return OTPResponse(result=False, message="Incorrect OTP. Please try again.")



    async def can_resend(self, email: str) -> OTPResponse:
        resend_count = await r.get(self._resend_key(email))
        last_resend = await r.get(self._last_resend_key(email))

        if resend_count and int(resend_count) >= self.MAX_RESENDS:
            return OTPResponse(result=False, message="You have reached the maximum number of resend attempts. Please try again later.")

        if last_resend:
            return OTPResponse(result=False, message="You must wait at least 60 seconds between OTP requests.")

        return OTPResponse(result=True, message="You can request a new OTP.")


    async def resend_otp(self, email: str):
        can_resend = await self.can_resend(email)
        if not can_resend.result:
            return can_resend
        otp = self.generate_otp()
        await r.set(self._otp_key(email), otp, ex=self.OTP_TTL_SECONDS)
        await r.incr(self._resend_key(email))
        await r.set(self._last_resend_key(email), datetime.now(timezone.utc).isoformat(), ex=self.RESEND_COOLDOWN)
        await r.set(self._otp_attempts_key(email), 0)
        return OTPResponse(result=True, message=otp)

    async def is_expired(self, email: str):
        first_seen = await r.get(self._first_seen_key(email))
        if not first_seen:
            return True
        seen_time = datetime.fromisoformat(first_seen)
        return datetime.now(timezone.utc) - seen_time > timedelta(seconds=self.MAX_LIFESPAN)

    async def delete_all(self, email: str):
        await r.delete(
            self._otp_key(email),
            self._data_key(email),
            self._resend_key(email),
            self._first_seen_key(email),
            self._last_resend_key(email)
        )

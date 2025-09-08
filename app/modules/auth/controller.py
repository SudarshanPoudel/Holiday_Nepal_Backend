import random
from fastapi import HTTPException , Request, Response
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
import secrets
import re

from app.modules.cities.repository import CityRepository
from app.modules.auth.email_template import get_otp_html, get_password_reset_html
from app.modules.storage.repository import ImageRepository
from app.modules.users.repository import UserRepository
from app.modules.auth.otp_service import OTPService
from app.modules.users.models import User
from app.core.config import settings
from app.modules.auth.schemas import Token, UserLogin
from app.modules.users.schemas import UserCreate, UserReadMinimal
from app.modules.auth.service import AuthService
from app.core.schemas import BaseResponse
from app.modules.auth.models import RefreshToken
from app.core.celery_tasks import send_email

class AuthController:
    otp_service = OTPService()

    async def register(self, user: UserCreate, db:AsyncSession):
        if not bool(re.fullmatch(r"[A-Za-z0-9_-]+", user.username)):
            raise HTTPException(status_code=400, detail="Invalid username, use only letters, numbers, - and _")

        result = await db.execute(select(User).where(User.email == user.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        result = await db.execute(select(User).where(User.username == user.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="This username is already taken..")
 

        hashed_password = AuthService.hash_password(user.password)
        user_data = user.model_dump()
        user_data["password"] = hashed_password

        otp = await self.otp_service.store_data_and_otp(user.email, user_data)
        # print(otp)
        html = get_otp_html(otp)
        send_email.apply_async(([user.email], "Verify Your Email", html), countdown=2)
        return BaseResponse(message="OTP sent to email. Verify within 30 minutes.", data={"email": user.email})

    async def verify_email(self, email: str, otp: str, db: AsyncSession):
        verify_otp = await self.otp_service.verify_otp(email, otp)
        if verify_otp.result:
            user_data = await self.otp_service.get_data(email)
            if not user_data:
                raise HTTPException(status_code=400, detail="User data expired or missing")

            user_obj = UserCreate(**user_data)
            user = await UserRepository(db=db).create(user_obj)
            await self.otp_service.delete_all(email)
            return BaseResponse(message="Email verified and account created.", data=UserReadMinimal.model_validate(user))
        else:
            raise HTTPException(status_code=400, detail=verify_otp.message)

    async def resend_verification_code(self, email: str):
        if await self.otp_service.is_expired(email):
            raise HTTPException(status_code=410, detail="No active OTP found")

        otp = await self.otp_service.resend_otp(email)
        if not otp.result:
            raise HTTPException(status_code=429, detail=otp.message)

        html = get_otp_html(otp.message)
        send_email.apply_async(([email], "Your New Verification Code", html), countdown=5)

        return BaseResponse(message="Verification code resent successfully.")


    async def login(self, user_login: UserLogin, db: AsyncSession, response: Response):
        result = await db.execute(
            select(User).where(
                or_(
                    User.email == user_login.email_or_username,
                    User.username == user_login.email_or_username
                )
            )
        )
        user = result.scalars().first()
        
        if user and AuthService.verify_password_hash(user_login.password, user.password):
            # Generate tokens
            role = "user"
            if user_login.email_or_username in settings.ADMIN_USERNAMES:
                role = "admin"
            access_token = AuthService.create_access_token({"user_id":user.id, "role": role})
            raw_refresh_token = AuthService.create_refresh_token({"user_id":user.id, "role": role})

            # Hash refresh token for DB
            hashed_token = AuthService.hash_refresh_token(raw_refresh_token)
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # Store refresh token in DB
            db_token = RefreshToken(
                user_id=user.id,
                token=hashed_token,
                expires_at=expires_at
            )
            db.add(db_token)
            await db.commit()

            # Set raw token as HTTPOnly cookie
            response.set_cookie(
                key="refresh_token",
                value=raw_refresh_token,
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=7 * 24 * 60 * 60
            )

            return BaseResponse(
                message="User logged in successfully",
                data=Token(access_token=access_token, token_type="Bearer", role=role, user_id=user.id),
                status_code=200
            )

        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    async def me(self, user_id: int, db: AsyncSession):
        user_repo = UserRepository(db=db)
        user = await user_repo.get(record_id=user_id, load_relations=["image"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_read = UserReadMinimal.model_validate(user, from_attributes=True)
        return BaseResponse(message="Profile fetched  success", data=user_read) 


    async def logout(self, request: Request, response: Response, db: AsyncSession):
        token = request.cookies.get("refresh_token")
        if not token:
            raise HTTPException(status_code=401, detail="Refresh token not found")

        # Verify the refresh token
        payload = await AuthService.verify_refresh_token(token, db)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Mark the refresh token as revoked in the database
        db_token = await db.execute(select(RefreshToken).where(RefreshToken.id == payload.get("token_id")))
        db_token.revoked = True
        await db.commit()

        # Clear the cookie
        response.delete_cookie("refresh_token")

        return BaseResponse(message="User logged out successfully", status_code=200)



    async def google_login_url(self) -> BaseResponse:
        url = await AuthService.get_google_login_url()
        return BaseResponse(message="Google login URL", data={"url": url})


    async def handle_google_callback(self, code: str, db: AsyncSession, response: Response) -> BaseResponse:
        user_info = await AuthService.handle_google_callback(code)
        email = user_info["email"]
        name = user_info["name"]
        username = await self.generate_unique_username(name, db)

        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create user
            random_password = secrets.token_urlsafe(32)
            hashed = AuthService.hash_password(random_password)
            user = User(username=username, email=email, password=hashed)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Login logic
        access_token = AuthService.create_access_token({"user_id":user.id, "role": "user"})
        raw_refresh_token = AuthService.create_refresh_token({"user_id":user.id, "role": "user"})
        hashed_token = AuthService.hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        db_token = RefreshToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=expires_at
        )
        db.add(db_token)
        await db.commit()

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=7 * 24 * 60 * 60
        )

        return BaseResponse(
            message="Google login successful",
            data=Token(access_token=access_token, token_type="Bearer", role="user", user_id=user.id),
            status_code=200
        )
    
    async def refresh_token(self, request: Request, response: Response, db: AsyncSession):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not found")

        # Verify the refresh token
        payload = await AuthService.verify_refresh_token(refresh_token, db)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = int(payload.get("user_id"))
        role = payload.get("role", "user")

        # Check if the refresh token exists in the database
        result = await db.execute(select(RefreshToken).where(RefreshToken.id == payload.get("token_id")))
        db_token = result.scalar_one_or_none()

        # Generate new access and refresh tokens
        access_token = AuthService.create_access_token({"user_id":user_id, "role": role})
        new_raw_refresh_token = AuthService.create_refresh_token({"user_id":user_id, "role": role})
        new_hashed_token = AuthService.hash_refresh_token(new_raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Update the refresh token in the database
        db_token.token = new_hashed_token
        db_token.expires_at = expires_at
        await db.commit()

        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=7 * 24 * 60 * 60
        )

        return BaseResponse(
            message="Token refreshed successfully",
            data=Token(access_token=access_token, token_type="Bearer", role=role, user_id=user_id),
            status_code=200
        )
    
    async def forget_password(self, email:str, db: AsyncSession):
        user = await UserRepository(db=db).get_by_fields({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            token = AuthService.create_url_safe_token(data={"user_id" : user.id})
            html = get_password_reset_html(token)
            send_email.apply_async(([user.email], "Password Reset Link", html), countdown=5)
            return BaseResponse(message="Password reset link sent successfully.")
        
    async def reset_password(self, token: str, new_password: str, db: AsyncSession):
        url_data = AuthService.decode_url_safe_token(token=token)
        if not url_data or "user_id" not in url_data:
            raise HTTPException(status_code=400, detail="Invalid or expired token.")

        user_id = url_data["user_id"]
        user_repo = UserRepository(db=db)
        user = await user_repo.get(record_id=user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        hashed_password = AuthService.hash_password(new_password)
        await user_repo.update_from_dict(record_id=user_id, data={"password": hashed_password})
        return BaseResponse(message="Password reset successful.")


    async def change_password(self, user_id: int, old_password: str, new_password: str, db: AsyncSession):
        user_repo = UserRepository(db=db)
        user = await user_repo.get(record_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if not AuthService.verify_password_hash(old_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password.")
        new_hashed = AuthService.hash_password(new_password)
        await user_repo.update_from_dict(record_id=user_id, data={"password": new_hashed})
        return BaseResponse(message="Password changed successfully.")


    async def generate_unique_username(self, name: str, db) -> str:
        base_username = re.sub(r"[^A-Za-z0-9_-]", "_", name).lower().strip("_")
        if not base_username:
            base_username = "user"

        like_pattern = f"{base_username}%"
        result = await db.execute(select(User.username).where(User.username.like(like_pattern)))
        existing_usernames = set(row[0] for row in result.fetchall())

        if base_username not in existing_usernames:
            return base_username

        attempts = 100
        for _ in range(attempts):
            rand_suffix = random.randint(1, 9999)
            candidate = f"{base_username}_{rand_suffix}"
            if candidate not in existing_usernames:
                return candidate

        return f"{base_username}_{secrets.token_hex(4)}"
    

    async def delete_account(self, user_id: int, password: str, db: AsyncSession):
        user_repo = UserRepository(db=db)
        user = await user_repo.get(record_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if not AuthService.verify_password_hash(password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect password.")

        await user_repo.delete(record_id=user_id)
        return BaseResponse(message="Account deleted successfully.")
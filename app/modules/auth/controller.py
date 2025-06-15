from fastapi import HTTPException , Request, Response
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
import secrets
import re

from app.modules.address.repository import MunicipalityRepository
from app.modules.auth.email_template import get_otp_html, get_password_reset_html
from app.modules.storage.repository import ImageRepository
from app.modules.users.repository import UserRepository
from app.modules.auth.otp_service import OTPService
from app.modules.users.models import User
from app.core.config import settings
from app.modules.auth.schemas import Token, UserLogin
from app.modules.users.schemas import UserCreate, UserRead
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

        if user.municipality_id:
            municipality_repo = MunicipalityRepository(db)
            municipality = await municipality_repo.get(record_id=user.municipality_id)
            if not municipality:
                raise HTTPException(status_code=404, detail="Municipality not found")

        hashed_password = AuthService.hash_password(user.password)
        user_data = user.model_dump()
        user_data["password"] = hashed_password

        otp = await self.otp_service.store_data_and_otp(user.email, user_data)

        html = get_otp_html(otp)
        send_email.apply_async(([user.email], "Verify Your Email", html), countdown=2)
        return BaseResponse(message="OTP sent to email. Verify within 30 minutes.")

    async def verify_email(self, email: str, otp: str, db: AsyncSession):
        verify_otp = await self.otp_service.verify_otp(email, otp)
        if verify_otp.result:
            user_data = await self.otp_service.get_data(email)
            if not user_data:
                raise HTTPException(status_code=400, detail="User data expired or missing")

            user_obj = UserCreate(**user_data)
            user = await UserRepository(db_session=db).create(user_obj)
            await self.otp_service.delete_all(email)
            return BaseResponse(message="Email verified and account created.", data={"id": user.id})
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
            access_token = AuthService.create_access_token({"user_id":user.id})
            raw_refresh_token = AuthService.create_refresh_token({"user_id":user.id})

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
                data=Token(access_token=access_token, token_type="Bearer"),
                status_code=200
            )

        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    async def me(self, user_id: int, db: AsyncSession):
        user_repo = UserRepository(db_session=db)
        user = await user_repo.get(record_id=user_id, load_relations=["image"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_read = UserRead.model_validate(user, from_attributes=True)
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

        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create user
            random_password = secrets.token_urlsafe(32)
            hashed = AuthService.hash_password(random_password)
            user = User(username=name, email=email, password=hashed)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Login logic
        access_token = AuthService.create_access_token({"user_id":user.id})
        raw_refresh_token = AuthService.create_refresh_token({"user_id":user.id})
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
            data=Token(access_token=access_token, token_type="Bearer"),
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
        
        user_id = int(payload.get("sub"))

        # Check if the refresh token exists in the database
        result = await db.execute(select(RefreshToken).where(RefreshToken.id == payload.get("token_id")))
        db_token = result.scalar_one_or_none()

        # Generate new access and refresh tokens
        access_token = AuthService.create_access_token({"user_id":user_id})
        new_raw_refresh_token = AuthService.create_refresh_token({"user_id":user_id})
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
            data=Token(access_token=access_token, token_type="Bearer"),
            status_code=200
        )
    
    async def forget_password(self, email:str, db: AsyncSession):
        user = await UserRepository(db_session=db).get_by_fields({"email": email})
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
        user_repo = UserRepository(db_session=db)
        user = await user_repo.get(record_id=user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        hashed_password = AuthService.hash_password(new_password)
        await user_repo.update_from_dict(record_id=user_id, data={"password": hashed_password})
        return BaseResponse(message="Password reset successful.")


    async def change_password(self, user_id: int, old_password: str, new_password: str, db: AsyncSession):
        user_repo = UserRepository(db_session=db)
        user = await user_repo.get(record_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if not AuthService.verify_password_hash(old_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password.")
        new_hashed = self.hash_password(new_password)
        await user_repo.update_from_dict(record_id=user_id, data={"password": new_hashed})
        return BaseResponse(message="Password changed successfully.")

from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.modules.auth.service import AuthService
from app.database.database import get_db
from app.core.config import settings
from app.modules.auth.models import RefreshToken
from passlib.context import CryptContext
from sqlalchemy import update
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.rstrip('/') in [
            "/auth/login", "/auth/register", "/auth/google_login",
            "/auth/google_callback", "/auth/refresh_token",
            "/auth/verify_email", "/auth/resend_otp",
            "/auth/forget_password", "/auth/change_password_with_token",
            "/docs", "/redoc", "/openapi.json"
        ]:
            return await call_next(request)

        token = request.headers.get("Authorization")
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJleHAiOjc3NDkyNzk2Mjd9.uww0CX8z1JC2z_SjtRCIkz7AtRPM_EMRHg70PR8SY1o"
        if not token:
            response = {"detail": "No token provided"}
            return Response(content=str(response), status_code=401)

        try:
            token = token.split(" ")[1] if token.startswith("Bearer ") else token
            user = AuthService.verify_access_token(token)

            if user:
                request.state.user_id = user.get("user_id")  # User ID from token
            else:
                response = {"detail": "Invalid token"}
                return Response(content=str(response), status_code=401)

        except ValueError:
            response = {"detail": "Invalid token format"}
            return Response(content=str(response), status_code=401)
        except Exception as e:
            response = {"detail": str(e)}
            return Response(content=str(response), status_code=401)

        return await call_next(request)

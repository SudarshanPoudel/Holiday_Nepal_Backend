import os
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.modules.auth.service import AuthService
from passlib.context import CryptContext

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
        load_dotenv()
        token = os.getenv("DEV_TOKEN")
        token = request.headers.get("Authorization") if not token else token
        if not token:
            response = HTTPException(status_code=401, detail="Token not found")
            return Response(content=str(response), status_code=401)

        try:
            token = token.split(" ")[1] if token.startswith("Bearer ") else token
            user = AuthService.verify_access_token(token)

            if user:
                request.state.user_id = user.get("user_id")  # User ID from token
            else:
                raise ValueError("Invalid token")

        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
        return await call_next(request)

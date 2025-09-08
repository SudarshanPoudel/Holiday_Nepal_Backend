import os
import re
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.modules.auth.service import AuthService
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        allowed_paths = [
            "",
            "/auth/login", "/auth/register", "/auth/refresh_token",
            "/auth/verify_email", "/auth/resend_otp",
            "/auth/forget_password", "/auth/reset_password",
            "/auth/oauth/google", "/auth/oauth/google/callback",
            "/docs", "/redoc", "/openapi.json", 
            "/cities", "/cities/nearest"
        ]

        # Add regex patterns for dynamic paths
        allowed_path_patterns = [
            
        ]

        path = request.url.path.rstrip('/')

        if path in allowed_paths or any(re.fullmatch(pattern, path) for pattern in allowed_path_patterns):
            return await call_next(request)
        

        load_dotenv()
        token = request.headers.get("Authorization") 
        # token = os.getenv("DEV_TOKEN") if not token else token
        if not token:
            raise HTTPException(status_code=401, detail="Token not found")

        try:
            token = token.split(" ")[1] if token.startswith("Bearer ") else token
            user = AuthService.verify_access_token(token)

            if user:
                request.state.user_id = user.get("user_id")  # User ID from token
                request.state.role = user.get("role", "user")
            else:
                raise ValueError("Invalid token")

        except ValueError as e:
            print(e)
            return Response(content="Invalid token", status_code=401)
        except Exception as e:
            raise e
        
        return await call_next(request)

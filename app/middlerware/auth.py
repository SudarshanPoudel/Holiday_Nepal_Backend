from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import re
from app.modules.auth.service import AuthService

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        allowed_paths = [
            "",
            "/auth/login", "/auth/register", "/auth/refresh_token",
            "/auth/verify_email", "/auth/resend_otp",
            "/auth/forget_password", "/auth/reset_password",
            "/auth/oauth/google", "/auth/oauth/google/callback",
            "/docs", "/redoc", "/openapi.json", 
            "/cities", "/cities/nearest",
        ]
        allowed_patterns = [
            # regex patterns for dynamic paths
        ]

        path = request.url.path.rstrip('/')
        if path in allowed_paths or any(re.fullmatch(p, path) for p in allowed_patterns):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if not token:
            return Response(content="Invalid token", status_code=401)  # <-- return Response instead of raising

        token = token.split(" ")[1] if token.startswith("Bearer ") else token
        user = AuthService.verify_access_token(token)

        if not user:
            return Response(content="Invalid token", status_code=401)  # <-- return Response instead of raising

        # Inject into request.state
        request.state.user_id = user.get("user_id")
        request.state.role = user.get("role", "user")

        return await call_next(request)

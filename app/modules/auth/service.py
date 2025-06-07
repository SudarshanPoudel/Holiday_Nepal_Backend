import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core.config import settings
from app.modules.auth.models import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from passlib.context import CryptContext
import hashlib
from itsdangerous import URLSafeTimedSerializer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(
    secret_key=settings.SECRET_KEY, salt="This is random salt hehehe"
)

CLIENT_SECRET_FILE = settings.GOOGLE_CLIENT_SECRET_FILE
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]
REDIRECT_URI = settings.FRONTEND_GOOGLE_AUTH_REDIRECT_URL

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod    
    def verify_refresh_token_hash(token: str, hashed: str) -> bool:
        return AuthService.hash_refresh_token(token) == hashed
    
    @staticmethod
    def create_access_token(to_encode: dict = {}, expires_delta: Optional[timedelta] = None) -> str:        
        # Use settings from config
        SECRET_KEY = settings.SECRET_KEY
        ALGORITHM = settings.ALGORITHM
        ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(to_encode: dict = {}, expires_delta: Optional[timedelta] = None) -> str:
        SECRET_KEY = settings.SECRET_KEY
        ALGORITHM = settings.ALGORITHM
        REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        SECRET_KEY = settings.SECRET_KEY
        ALGORITHM = settings.ALGORITHM

        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidSignatureError:
            return None
        except jwt.PyJWTError:
            return None


    @staticmethod
    async def verify_refresh_token(token: str, db: AsyncSession) -> Optional[tuple[dict, int]]:
        SECRET_KEY = settings.SECRET_KEY
        ALGORITHM = settings.ALGORITHM
       
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        
        if not user_id:
            return None

        # Fetch all refresh tokens for the user
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
        )
        refresh_tokens = result.scalars().all()

        try:
            # Check if provided token matches any hashed one
            for rt in refresh_tokens:
                if AuthService.verify_refresh_token_hash(token, rt.token):
                    if rt.expires_at < datetime.now(timezone.utc):
                        return None  # Expired
                    payload["token_id"] = rt.id
                    return payload  # Return payload and token ID

            return None  # No match found

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidSignatureError:
            return None
        except jwt.PyJWTError:
            return None

    @staticmethod
    async def get_google_login_url() -> str:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        return auth_url

    @staticmethod
    async def handle_google_callback(code: str) -> dict:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        idinfo = id_token.verify_oauth2_token(
            credentials._id_token,
            requests.Request(),
            flow.client_config["client_id"]
        )
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name")
        }

    @staticmethod
    def create_url_safe_token(data: dict):
        token = serializer.dumps(data)
        return token

    @staticmethod
    def decode_url_safe_token(token:str):
        try:
            token_data = serializer.loads(token, max_age = 600)
            return token_data
        except Exception as e:
            return None
        
    
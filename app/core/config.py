from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@db:5432/postgres"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://redis:6379"

    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_FROM:str
    MAIL_FROM_NAME:str
    MAIL_SERVER:str

    ENVIRONMENT: str = "local"
    
    FRONTEND_GOOGLE_AUTH_REDIRECT_URL: str = "http://localhost:3000"
    FRONTEND_FORGET_PASSWORD_URL:str = "http://localhost:3000/forget_password"
    DOMAIN: str = "http://127.0.0.1:8000"
    class Config:
        env_file = ".env" if os.getenv("DOCKERIZED") != "1" else None

settings = Settings()


broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL
broker_connection_retry_on_startup = True
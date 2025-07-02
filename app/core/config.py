from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@db:5432/postgres"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 100000000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://redis:6379"

    AWS_ACCESS_KEY_ID:str = "test"
    AWS_SECRET_ACCESS_KEY:str = "test"
    AWS_REGION:str="us-east-1" 
    AWS_STORAGE_BUCKET_NAME:str = "holidaynepal"
    USE_LOCAL_STACK:bool = True

    GOOGLE_CLIENT_SECRET_FILE:str = "credentials.json"

    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_FROM:str
    MAIL_FROM_NAME:str
    MAIL_SERVER:str

    ENVIRONMENT: str = "local"
    
    FRONTEND_GOOGLE_AUTH_REDIRECT_URL: str = "http://localhost:3000"
    FRONTEND_FORGET_PASSWORD_URL:str = "http://localhost:3000/forget_password"
    DOMAIN: str = "http://127.0.0.1:8000"

    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"

    class Config:
        env_file = ".env" if os.getenv("DOCKERIZED") != "1" else None

settings = Settings()


broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL
broker_connection_retry_on_startup = True
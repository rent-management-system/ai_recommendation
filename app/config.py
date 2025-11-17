from pydantic_settings import BaseSettings
from pydantic import field_validator
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/rental_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "your_jwt_secret"
    GEBETA_API_KEY: str = "your_gebeta_key"
    GEMINI_API_KEY: str = "your_gemini_key"
    USER_MANAGEMENT_URL: str = "https://rent-managment-system-user-magt.onrender.com"
    SEARCH_FILTERS_URL: str = "http://search-filters:8000"

    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/rental_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "your_jwt_secret"
    GEBETA_API_KEY: str = "your_gebeta_key"
    GEMINI_API_KEY: str = "your_gemini_key"
    USER_MANAGEMENT_URL: str = "http://user-management:8000"
    SEARCH_FILTERS_URL: str = "http://search-filters:8000"
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

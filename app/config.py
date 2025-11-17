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

    @field_validator("DATABASE_URL")
    def encode_database_url(cls, v):
        """
        Parses and re-encodes the database URL to handle special characters in the password
        and adds sslmode=require.
        """
        if v:
            try:
                # Parse the URL.
                url = URL.create(v)
                # Unconditionally add sslmode=require to the query parameters
                query = dict(url.query)
                query['sslmode'] = 'require'
                url = url.set(query=query)
                # Return the string representation of the URL.
                return str(url)
            except Exception:
                # If parsing fails, return the original value.
                return v
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

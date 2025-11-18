import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

DB_URL = settings.DATABASE_URL
if not DB_URL:
    raise RuntimeError("DATABASE_URL not set")

# Create an SSLContext as recommended for asyncpg
ssl_ctx = ssl.create_default_context()
# Allow self-signed certs for development
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# Create a single, shared async engine for the application
engine = create_async_engine(
    DB_URL,
    poolclass=NullPool,  # Recommended for serverless/async environments
    connect_args={"ssl": ssl_ctx},
    future=True,
)

# Create a session factory to generate new sessions
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency for getting a session in FastAPI routes
async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session

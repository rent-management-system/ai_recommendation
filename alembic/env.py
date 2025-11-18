import sys
from pathlib import Path
import os

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from alembic import context
# from app.config import settings # Removed
from app.models import Base


# (Optional) load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

config = context.config
# config.set_main_option("sqlalchemy.url", settings.DATABASE_URL) # Removed
fileConfig(config.config_file_name)

# read DB URL directly (don't pass through configparser)
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL not set. Export it (or add in .env).")

# If user provided an async URL (app uses asyncpg), derive a sync URL for alembic:
# e.g. postgresql+asyncpg://...  ->  postgresql://...
if "+asyncpg" in db_url:
    sync_db_url = db_url.replace("+asyncpg", "")
else:
    sync_db_url = db_url

# Ensure sslmode present once
if "sslmode=" not in sync_db_url.lower():
    sep = "&" if "?" in sync_db_url else "?"
    sync_db_url = f"{sync_db_url}{sep}sslmode=require"

# Create sync engine for alembic work (no pooling to avoid pooler issues)
engine = create_engine(
    sync_db_url,
    poolclass=NullPool,
    future=True,
)

# Removed async_db_url and sync_db_url definitions

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is still acceptable
    here as it will be used to render the SQL DDL statements
    to the script output.
    """
    url = sync_db_url # Changed to sync_db_url
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=Base.metadata, # Use Base.metadata
        compare_type=True,
        # process_revision_directives=process_revision_directives, # Commented out
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario, we need to create a synchronous Engine
    and associate a connection with the context.
    """
    connectable = engine  # use the sync engine we just created

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata) # Use Base.metadata
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import google.generativeai as genai
from app.config import settings
from structlog import get_logger
from pybreaker import CircuitBreaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict

logger = get_logger()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

# Define the properties table schema as a string for Gemini's knowledge base
PROPERTIES_TABLE_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'propertystatus') THEN
        CREATE TYPE propertystatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
    END IF;
END$;

CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    amenities JSONB DEFAULT '[]'::jsonb,
    photos JSONB DEFAULT '[]'::jsonb,
    status propertystatus NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fts tsvector
);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Drop the trigger if it exists to avoid errors on re-run
DROP TRIGGER IF EXISTS set_timestamp ON properties;

-- Create the trigger
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON properties
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_properties_user_id ON properties (user_id);
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties (status);
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties (location);
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties (price);

-- Full-text search index
CREATE INDEX IF NOT EXISTS fts_idx ON properties USING gin(fts);

CREATE OR REPLACE FUNCTION update_fts_column() RETURNS trigger AS $
BEGIN
  NEW.fts := to_tsvector('english', NEW.title || ' ' || NEW.description);
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_fts ON properties;

CREATE TRIGGER update_fts
BEFORE INSERT OR UPDATE ON properties
FOR EACH ROW EXECUTE PROCEDURE update_fts_column();
"""

@breaker
async def generate_sql_query(user_query: str) -> str:
    """
    Generates an SQL query based on the user's natural language query and the properties table schema.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    You are an expert in PostgreSQL. Your task is to convert a natural language query into an SQL SELECT statement for the 'properties' table.
    The table schema is as follows:

    {PROPERTIES_TABLE_SCHEMA}

    Consider the 'fts' column for full-text search when relevant.
    Ensure the generated SQL query is valid PostgreSQL syntax and only selects relevant columns.
    Do NOT include any explanations, just the SQL query.

    User query: "{user_query}"

    SQL Query:
    """
    try:
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        # Basic validation to ensure it's a SELECT query
        if not sql_query.lower().startswith("select"):
            raise ValueError("Generated query is not a SELECT statement.")
        return sql_query
    except Exception as e:
        await logger.error("Gemini API failed to generate SQL query", error=str(e))
        raise

async def execute_sql_query(sql_query: str, db: AsyncSession) -> List[Dict]:
    """
    Executes the given SQL query against the PostgreSQL database and returns the results.
    """
    try:
        result = await db.execute(text(sql_query))
        # For SELECT statements, fetch all rows
        rows = result.fetchall()
        # Convert Row objects to dictionaries
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        await logger.error("Failed to execute SQL query", sql_query=sql_query, error=str(e))
        raise

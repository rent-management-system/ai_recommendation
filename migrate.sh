#!/usr/bin/env bash
set -euo pipefail

# Go to script directory so paths are correct
cd "$(dirname "${BASH_SOURCE[0]}")"

# --- Load .env safely ---
if [ -f ".env" ]; then
  echo "Loading variables from .env ..."
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
else
  echo ".env file not found!"
  exit 1
fi

# ensure DATABASE_URL exists
: "${DATABASE_URL:?DATABASE_URL must be defined in .env}"

echo "DATABASE_URL loaded."

# --- Run Alembic migrations ---
echo "Running Alembic migrations..."
alembic upgrade head

# --- Convert asyncpg URL to sync for psql ---
if [[ "$DATABASE_URL" == *"+asyncpg"* ]]; then
  SYNC_DATABASE_URL="${DATABASE_URL//+asyncpg/}"
else
  SYNC_DATABASE_URL="$DATABASE_URL"
fi

echo "Using sync DB URL for psql."

# --- URL-encode the password for psql ---
ENCODED_URL="$SYNC_DATABASE_URL"
if [[ "$SYNC_DATABASE_URL" =~ ^([^:]+)://([^:]+):([^@]+)@(.+)$ ]]; then
  SCHEME="${BASH_REMATCH[1]}"
  USER="${BASH_REMATCH[2]}"
  PASSWORD="${BASH_REMATCH[3]}"
  HOST_PORT_DB="${BASH_REMATCH[4]}"

  # URL-encode the password (specifically for the '/' character)
  ENCODED_PASSWORD="${PASSWORD//\//%2F}"

  # Reassemble the URL
  ENCODED_URL="${SCHEME}://${USER}:${ENCODED_PASSWORD}@${HOST_PORT_DB}"
  echo "URL-encoded password for psql."
fi

# --- Seed database ---
echo "Seeding database..."
psql "$ENCODED_URL" -f sql/seed.sql

echo "Migration + Seed completed successfully."

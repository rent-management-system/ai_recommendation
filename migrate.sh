#!/bin/bash
alembic upgrade head
psql $DATABASE_URL -f sql/seed.sql

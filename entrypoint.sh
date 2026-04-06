#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "$SEED_ON_STARTUP" = "true" ]; then
    echo "Seed data enabled. Running seed..."
    python -m app.seed.seed_data
else
    echo "Seed data disabled. Set SEED_ON_STARTUP=true to enable."
fi

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

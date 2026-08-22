#!/bin/bash

# ── Cleanup on exit ──────────────────────────────────────────
# Handles shutting down the backend process gracefully
cleanup() {
    if [[ -n "$BACKEND_PID" ]]; then
        echo "Shutting down backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Port kill ────────────────────────────────────────────────
echo "Killing any process on port 8000..."
if command -v fuser >/dev/null 2>&1; then
    fuser -k 8000/tcp 2>/dev/null || true
fi
sleep 1

# ── Virtual Environment Setup ────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using uv if available, otherwise venv..."
    if command -v uv >/dev/null 2>&1; then
        uv venv .venv
    else
        python3 -m venv .venv
    fi
fi

# Activate the virtual environment 
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Could not find .venv/bin/activate"
    exit 1
fi

# ── Requirements Installation ────────────────────────────────
if command -v uv >/dev/null 2>&1; then
    echo "installing requirements..."
    uv pip install -r requirements.txt
else
    echo "installing requirements..."
    pip install -r requirements.txt
fi

# ── Database Setup ───────────────────────────────────────────
docker-compose down
docker-compose up -d

# Wait for the database to be ready
sleep 3

# ── Django database seeding ────────────────────────────────────────
python manage.py migrate
python manage.py create_default_admin
python manage.py seed_books

# ── Start Backend ────────────────────────────────────────────
echo "Starting backend..."
python manage.py runserver
BACKEND_PID=$!

# Verify backend actually started
sleep 1
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend failed to start. Check logs above."
    exit 1
fi

# Wait until port 8000 is accepting connections
echo "Waiting for backend to be ready..."
while ! nc -z localhost 8000; do sleep 0.5; done
echo "Backend is up on port 8000."

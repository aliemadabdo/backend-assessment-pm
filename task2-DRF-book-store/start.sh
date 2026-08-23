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
#!/bin/bash

kill_port() {
    local port=$1
    local pids
    pids=$(lsof -t -i :"$port" 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "Killing processes on port $port: $pids"
        kill -9 $pids
    else
        echo "Nothing running on port $port"
    fi
    sleep 1
}

# ── Port kill ────────────────────────────────────────────────
kill_port 8000
kill_port 5432

# ── Virtual Environment Setup ────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using uv if available, otherwise venv..."
    if command -v uv >/dev/null 2>&1; then
        uv venv .venv --python 3.12
    else
        python3.12 -m venv .venv
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
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "Docker Compose is required but not found on PATH."
    exit 1
fi

$COMPOSE_CMD down
$COMPOSE_CMD up -d db

# Wait for PostgreSQL to accept connections before Django starts working
until $COMPOSE_CMD exec -T db pg_isready -U "${POSTGRES_USER:-bookstore}" -d "${POSTGRES_DB:-bookstore}" >/dev/null 2>&1; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

# ── Django database seeding ────────────────────────────────────────
python manage.py migrate
python manage.py create_default_admin
python manage.py seed_books

# ── Start Backend ────────────────────────────────────────────
echo "Starting backend..."
python manage.py runserver 0.0.0.0:8000
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

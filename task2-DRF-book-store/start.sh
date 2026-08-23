#!/bin/bash

# ── COLOR CODES ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Cleanup on exit ──────────────────────────────────────────
# Handles shutting down the backend process gracefully
cleanup() {
    if [[ -n "$BACKEND_PID" ]]; then
        echo -e "${YELLOW}Shutting down backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Port kill ────────────────────────────────────────────────
kill_port() {
    local port=$1
    local pids
    pids=$(lsof -t -i :"$port" 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Killing processes on port $port: $pids${NC}"
        kill -9 $pids
    else
        echo -e "${CYAN}Nothing running on port $port${NC}"
    fi
    sleep 1
}

kill_port 8000
kill_port 5432

# ── Virtual Environment Setup ────────────────────────────────
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment using uv if available, otherwise venv...${NC}"
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
    echo -e "${RED}ERROR: Could not find .venv/bin/activate${NC}"
    exit 1
fi

# ── Requirements Installation ────────────────────────────────
if command -v uv >/dev/null 2>&1; then
    echo -e "${BLUE}Installing requirements...${NC}"
    uv pip install -r requirements.txt
else
    echo -e "${BLUE}Installing requirements...${NC}"
    pip install -r requirements.txt
fi

# ── Database Setup ───────────────────────────────────────────
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Docker Compose is required but not found on PATH.${NC}"
    exit 1
fi

$COMPOSE_CMD down
$COMPOSE_CMD up -d db

# Wait for PostgreSQL to accept connections before Django starts working
until $COMPOSE_CMD exec -T db pg_isready -U "${POSTGRES_USER:-bookstore}" -d "${POSTGRES_DB:-bookstore}" >/dev/null 2>&1; do
    echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
    sleep 2
done

# ── Django database seeding ────────────────────────────────────────
echo -e "${BLUE}Applying Django migrations...${NC}"
python manage.py migrate

echo -e "${BLUE}Creating default admin user...${NC}"
python manage.py create_default_admin

echo -e "${BLUE}Seeding books...${NC}"
python manage.py seed_books

# ── Start Backend ────────────────────────────────────────────
echo -e "${GREEN}Starting backend...${NC}"
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# Verify backend actually started
sleep 1
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}ERROR: Backend failed to start. Check logs above.${NC}"
    exit 1
fi

# Wait until port 8000 is accepting connections
echo -e "${CYAN}Waiting for backend to be ready...${NC}"
while ! nc -z localhost 8000; do sleep 0.5; done
echo -e "${GREEN}Backend is up on port 8000.${NC}"

echo ""
echo -e "${CYAN}Swagger UI:  ${YELLOW}http://127.0.0.1:8000/api/schema/swagger-ui/#/${NC}"
echo -e "${CYAN}Django Admin: ${YELLOW}http://127.0.0.1:8000/admin/${NC}"
echo ""
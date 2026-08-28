#!/usr/bin/env bash

# ==============================================================================
# AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform
# Unified Runner Script (Backend + Frontend)
# ==============================================================================

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Determine repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo " 🛡️  AI-Powered Email Threat Detection & Forensic Platform"
echo "======================================================================"
echo -e "${NC}"

# ------------------------------------------------------------------------------
# 1. Dependency & Environment Checks
# ------------------------------------------------------------------------------

# Check for Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Error: Python is not installed or not in PATH.${NC}"
    exit 1
fi

# Check for Node and npm
if ! command -v node &>/dev/null; then
    echo -e "${RED}❌ Error: Node.js is not installed or not in PATH.${NC}"
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo -e "${RED}❌ Error: npm is not installed or not in PATH.${NC}"
    exit 1
fi

# Virtual Environment Setup
VENV_DIR=""
if [ -d "$SCRIPT_DIR/.venv" ]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
elif [ -d "$SCRIPT_DIR/backend/.venv" ]; then
    VENV_DIR="$SCRIPT_DIR/backend/.venv"
else
    echo -e "${YELLOW}⚡ No virtual environment detected. Creating .venv...${NC}"
    $PYTHON_CMD -m venv "$SCRIPT_DIR/.venv"
    VENV_DIR="$SCRIPT_DIR/.venv"
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Python virtual environment active (${VENV_DIR})${NC}"

# Check backend Python dependencies
if ! python -c "import fastapi, uvicorn, sqlalchemy" &>/dev/null; then
    echo -e "${YELLOW}⚡ Installing Backend dependencies (backend/gateway/requirements.txt)...${NC}"
    pip install -r "$SCRIPT_DIR/backend/gateway/requirements.txt"
    echo -e "${GREEN}✓ Backend dependencies installed.${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies already satisfied.${NC}"
fi

# Seed Demo Admin if script is available
if [ -f "$SCRIPT_DIR/backend/gateway/scripts/seed_demo_admin.py" ]; then
    echo -e "${CYAN}⚡ Verifying demo admin account...${NC}"
    (cd "$SCRIPT_DIR/backend/gateway" && python scripts/seed_demo_admin.py) || true
fi

# Check Frontend npm dependencies
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}⚡ Installing Frontend dependencies (npm install in frontend/)...${NC}"
    (cd "$SCRIPT_DIR/frontend" && npm install)
    echo -e "${GREEN}✓ Frontend dependencies installed.${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies already satisfied.${NC}"
fi

# ------------------------------------------------------------------------------
# 2. Port Check / Advisory
# ------------------------------------------------------------------------------

check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Warning: Port $port ($name) appears to be in use. It might cause a startup collision.${NC}"
    fi
}

check_port 8001 "Backend Gateway"
check_port 5173 "Frontend Vite"

# ------------------------------------------------------------------------------
# 3. Graceful Shutdown Trap
# ------------------------------------------------------------------------------

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Received shutdown signal. Stopping all servers...${NC}"
    
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${CYAN}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${CYAN}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi

    wait 2>/dev/null || true
    echo -e "${GREEN}✓ All processes stopped cleanly. Goodbye!${NC}"
    exit 0
}

trap cleanup INT TERM EXIT

# ------------------------------------------------------------------------------
# 4. Start Backend & Frontend
# ------------------------------------------------------------------------------

echo ""
echo -e "${BLUE}${BOLD}🚀 Starting Backend Gateway (port 8001)...${NC}"
(
    cd "$SCRIPT_DIR/backend/gateway"
    python -m uvicorn app.main:app --reload --port 8001
) &
BACKEND_PID=$!

echo -e "${BLUE}${BOLD}🚀 Starting Frontend Dashboard (Vite)...${NC}"
(
    cd "$SCRIPT_DIR/frontend"
    npm run dev
) &
FRONTEND_PID=$!

# Give servers a moment to initialize
sleep 2

# ------------------------------------------------------------------------------
# 5. Service Status & Access Summary
# ------------------------------------------------------------------------------

echo ""
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}  ✨ Services are running! Access the platform at:                    ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "  🌐 ${BOLD}Frontend Dashboard:${NC}  ${CYAN}http://localhost:5173${NC}"
echo -e "  ⚙️  ${BOLD}Backend API Docs:${NC}    ${CYAN}http://localhost:8001/docs${NC}"
echo -e "  📖 ${BOLD}API ReDoc:${NC}           ${CYAN}http://localhost:8001/redoc${NC}"
echo -e "  ❤️  ${BOLD}Health Check:${NC}        ${CYAN}http://localhost:8001/health${NC}"
echo ""
echo -e "  🔑 ${BOLD}Demo Login Credentials:${NC}"
echo -e "     Email:    ${BOLD}admin@aiemil.demo${NC}"
echo -e "     Password: ${BOLD}AIEMIL-Demo-2026!${NC}"
echo -e "     Tenant:   ${BOLD}demo-tenant${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "${YELLOW}👉 Press [Ctrl+C] at any time to gracefully shut down both services.${NC}"
echo ""

# Wait indefinitely for child processes
wait "$BACKEND_PID" "$FRONTEND_PID"

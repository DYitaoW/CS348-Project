#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="$ROOT_DIR/backend"

# Start backend
(
  cd "$BACKEND_DIR"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install -r requirements.txt

  # Default to SQLite if DATABASE_URL is not set
  if [ -z "${DATABASE_URL:-}" ]; then
    export DATABASE_URL=sqlite:///soccer.db
  fi

  python3 app.py
) &

BACKEND_PID=$!

# Start frontend
(
  cd "$ROOT_DIR"
  npm install
  npm start
) &

FRONTEND_PID=$!

# Cleanup on exit
trap 'kill $BACKEND_PID $FRONTEND_PID' EXIT

wait

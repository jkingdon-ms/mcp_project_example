#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/server"

echo "Installing server dependencies..."
pip install -r "$SERVER_DIR/requirements.txt"

echo "Starting server at http://localhost:8080/v2/ui/ ..."
cd "$SERVER_DIR" 
python -m openapi_server

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Generating Python Flask server..."
openapi-generator-cli generate \
  -i "$SCRIPT_DIR/swagger.json" \
  -g python-flask \
  -o "$SCRIPT_DIR/server"

echo "Generating Python client..."
openapi-generator-cli generate \
  -i "$SCRIPT_DIR/swagger.json" \
  -g python \
  -o "$SCRIPT_DIR/client"

echo "Done."

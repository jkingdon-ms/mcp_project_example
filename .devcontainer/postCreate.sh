#!/bin/bash
set -e

python -m venv .venv
source .venv/bin/activate
find . -name requirements.txt -exec pip install -r {} \;

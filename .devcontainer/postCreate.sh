#!/bin/bash
set -e

python -m venv .venv
source .venv/bin/activate
pip install -e .
find . -name requirements.txt -exec pip install -r {} \;

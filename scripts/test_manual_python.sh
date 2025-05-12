#!/usr/bin/env bash

set -e;

# Check you're in project root
if [ ! -f "cli/ascii_art_logo.txt" ]; then
  echo "Please run this script from the project root directory."
  exit 1
fi

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi


export PYTHONPATH="${PWD}:$PYTHONPATH"

echo "Running Python tests..."

pytest backend/tests/python_tests -v;
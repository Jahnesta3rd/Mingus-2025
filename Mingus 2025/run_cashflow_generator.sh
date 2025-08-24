#!/bin/bash

# Search your home directory for the first folder that contains generate_schedule.py
MATCH=$(find ~ -type f -name "generate_schedule.py" -exec dirname {} \; | head -n 1)

if [ -z "$MATCH" ]; then
  echo "Could not find generate_schedule.py on your system."
  exit 1
fi

echo "Found project folder at: $MATCH"
cd "$MATCH"

echo "Running test_run.py..."
python3 test_run.py

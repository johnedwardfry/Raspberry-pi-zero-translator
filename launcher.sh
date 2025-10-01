#!/bin/bash
set -e

# --- THIS BLOCK IS THE FIX ---
# Manually create and set the XDG_RUNTIME_DIR for the user
USER_ID=$(id -u)
RUNTIME_DIR="/tmp/runtime-user-$USER_ID"
if [ ! -d "$RUNTIME_DIR" ]; then
    mkdir -p "$RUNTIME_DIR"
    chmod 700 "$RUNTIME_DIR"
fi
export XDG_RUNTIME_DIR="$RUNTIME_DIR"
# --- END OF FIX ---

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate the virtual environment and run the Python script
source .venv/bin/activate
python3 main.py > translator_output.log 2>&1
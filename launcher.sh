#!/bin/bash
set -e

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate the virtual environment and run the Python script,
# redirecting all output and errors to a log file.
source .venv/bin/activate
python3 main.py > translator_output.log 2>&1
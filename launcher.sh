#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate the virtual environment and run the Python script
source .venv/bin/activate
python3 main.py
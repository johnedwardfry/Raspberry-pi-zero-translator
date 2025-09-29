#!/bin/bash

echo "--- Starting Full Translator Project Setup ---"
cd "$(dirname "$0")"

# --- Step 1: Install Dependencies ---
echo "[1/2] Creating virtual environment and installing packages..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate
echo "Dependencies installed successfully."

# --- Step 2: Configure Autostart ---
echo "[2/2] Configuring application to run on boot..."
AUTOSTART_FILE="$HOME/.config/lxsession/LXDE-pi/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"
LAUNCHER_CMD="@lxterminal -e $LAUNCHER_PATH"

# Create the config directory and file if they don't exist
mkdir -p "$(dirname "$AUTOSTART_FILE")"
touch "$AUTOSTART_FILE"

# Check if the command is already in the autostart file
if ! grep -qF "$LAUNCHER_CMD" "$AUTOSTART_FILE"; then
    echo "Adding launcher to autostart file..."
    echo "$LAUNCHER_CMD" >> "$AUTOSTART_FILE"
    echo "Autostart configured."
else
    echo "Application is already configured to autostart."
fi

echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. Edit the 'config.ini' file to add your API key."
echo "2. Reboot your Raspberry Pi with 'sudo reboot'."
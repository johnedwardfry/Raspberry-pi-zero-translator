#!/bin/bash

echo "--- Starting Full Translator Project Setup ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
echo "[1/3] Updating package list and installing system dependencies..."
sudo apt-get update
# ADDED python3-dev to this line
sudo apt-get install -y portaudio19-dev python3-dev
echo "System dependencies installed."

# --- Step 2: Install Python Dependencies ---
echo "[2/3] Creating virtual environment and installing packages..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate
echo "Python libraries installed successfully."

# --- Step 3: Configure Autostart ---
echo "[3/3] Configuring application to run on boot..."
AUTOSTART_FILE="$HOME/.config/lxsession/LXDE-pi/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"
LAUNCHER_CMD="@lxterminal -e $LAUNCHER_PATH"

mkdir -p "$(dirname "$AUTOSTART_FILE")"
touch "$AUTOSTART_FILE"

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
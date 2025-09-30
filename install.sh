#!/bin/bash
set -e

echo "--- Starting Project Setup on Full OS ---"
cd "$(dirname "$0")"

# --- Step 1: Install System and Python Dependencies ---
echo "[1/2] Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
echo "Dependencies installed."

# --- Step 2: Configure Desktop Autostart ---
echo "[2/2] Configuring application to run on boot..."
AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
AUTOSTART_FILE="$AUTOSTART_DIR/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Create the config directory if it doesn't exist
mkdir -p "$AUTOSTART_DIR"

# Add the launcher if it's not already there
if ! grep -qF "$LAUNCHER_PATH" "$AUTOSTART_FILE" 2>/dev/null; then
    echo "@$LAUNCHER_PATH" >> "$AUTOSTART_FILE"
    echo "Autostart configured."
else
    echo "Application is already configured to autostart."
fi

echo ""
echo "--- ✅ Installation Complete ---"
echo "Reboot your Raspberry Pi with 'sudo reboot' to start the translator."
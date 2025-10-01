#!/bin/bash
set -e

echo "--- Starting Full Translator Project Setup (System-wide Autostart) ---"
cd "$(dirname "$0")"

# --- Step 1: Install Dependencies ---
echo "[1/3] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev ffmpeg
echo "System dependencies installed."

# --- Step 2: Install Python Dependencies ---
echo "[2/3] Creating virtual environment and installing packages..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
# Check if requirements.txt exists before trying to install
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Skipping pip install."
fi
deactivate
echo "Python libraries installed."

# --- Step 3: Configure System-Wide Desktop Autostart ---
echo "[3/3] Configuring system-wide autostart..."

# --- THIS BLOCK CONTAINS THE FINAL FIX ---
# We now use a more direct command that doesn't rely on lxterminal.
AUTOSTART_FILE="/etc/xdg/lxsession/LXDE-pi/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"
# This is the simplified command. Note the '&' to run in the background.
LAUNCHER_CMD="$LAUNCHER_PATH &"

# We need to remove the old command if it exists, before adding the new one.
# The `|| true` prevents an error if the file doesn't exist yet.
sudo sed -i '/launcher.sh/d' "$AUTOSTART_FILE" || true

# Add the new, simplified command to the autostart file.
echo "Adding launcher to system-wide autostart file..."
echo "$LAUNCHER_CMD" | sudo tee -a "$AUTOSTART_FILE" > /dev/null
echo "Autostart configured."
# --- END OF FIX ---

echo ""
echo "--- ✅ Installation Complete ---"
echo "This is the final and most reliable method. Please reboot now."
echo "Command: sudo reboot"
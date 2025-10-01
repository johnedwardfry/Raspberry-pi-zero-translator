#!/bin/bash
set -e

echo "--- Starting Full Translator Project Setup (System-wide Autostart) ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
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
# This edits the main desktop session file directly.
AUTOSTART_FILE="/etc/xdg/lxsession/LXDE-pi/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"
LAUNCHER_CMD="@lxterminal -e $LAUNCHER_PATH"

# Check if the command is already in the autostart file before adding it
if ! grep -qF "$LAUNCHER_CMD" "$AUTOSTART_FILE" 2>/dev/null; then
    echo "Adding launcher to system-wide autostart file..."
    # Use 'tee -a' with sudo to append the line to the protected file
    echo "$LAUNCHER_CMD" | sudo tee -a "$AUTOSTART_FILE" > /dev/null
    echo "Autostart configured."
else
    echo "Application is already configured in system-wide autostart."
fi
# --- END OF FIX ---

echo ""
echo "--- ✅ Installation Complete ---"
echo "This is the final and most reliable method. Please reboot now."
echo "Command: sudo reboot"
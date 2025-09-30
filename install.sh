#!/bin/bash
set -e

echo "--- Starting Full Translator Project Setup (Desktop Autostart) ---"
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

# --- Step 3: Configure Desktop Autostart ---
echo "[3/3] Configuring application to run on boot..."

# --- THIS BLOCK CONTAINS THE FINAL FIX ---
# This creates a .desktop file in the correct autostart directory for the full desktop OS.
AUTOSTART_DIR="/home/$SUDO_USER/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/translator.desktop"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Create the directory as the correct user
sudo -u $SUDO_USER mkdir -p "$AUTOSTART_DIR"

# Create the .desktop file as the correct user
sudo -u $SUDO_USER tee "$DESKTOP_FILE" > /dev/null <<EOF
[Desktop Entry]
Name=Audio Translator
Comment=Starts the audio translator application
Exec=$LAUNCHER_PATH
Terminal=true
Type=Application
EOF
# --- END OF FIX ---

echo "Autostart configured."
echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. If you haven't already, edit 'config.ini' with your API key."
echo "2. Reboot your Raspberry Pi with 'sudo reboot'."
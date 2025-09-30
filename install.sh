#!/bin/bash
set -e

echo "--- Starting Full Translator Project Setup (Openbox Autostart) ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
echo "[1/3] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev xserver-xorg xinit openbox xserver-xorg-input-all lightdm
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

# --- Step 3: Configure Openbox Autostart ---
echo "[3/3] Configuring Openbox to launch the translator..."

# --- THIS BLOCK CONTAINS THE FIX ---
# It now uses the $SUDO_USER variable instead of a hardcoded 'pi' username.
AUTOSTART_DIR="/home/$SUDO_USER/.config/openbox"
AUTOSTART_FILE="$AUTOSTART_DIR/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Create the directory as the correct user
sudo -u $SUDO_USER mkdir -p "$AUTOSTART_DIR"

# Create the autostart file as the correct user
sudo -u $SUDO_USER tee "$AUTOSTART_FILE" > /dev/null <<EOF
# Launch the translator application
$LAUNCHER_PATH &
EOF
# --- END OF FIX ---

echo "Autostart configured."
echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. If you haven't already, edit the 'config.ini' file with your API key."
echo "2. Please ensure the Pi is set to 'Desktop Autologin' in raspi-config."
echo "3. Reboot your Raspberry Pi with 'sudo reboot'."
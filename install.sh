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
pip install -r requirements.txt
deactivate
echo "Python libraries installed."

# --- Step 3: Configure Openbox Autostart ---
echo "[3/3] Configuring Openbox to launch the translator..."
AUTOSTART_DIR="/home/pi/.config/openbox"
AUTOSTART_FILE="$AUTOSTART_DIR/autostart"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Create the directory as the 'pi' user if it doesn't exist
sudo -u pi mkdir -p "$AUTOSTART_DIR"

# Create the autostart file with the command to run our launcher
# The '&' at the end is important to run it in the background
sudo -u pi tee "$AUTOSTART_FILE" > /dev/null <<EOF
# Launch the translator application
$LAUNCHER_PATH &
EOF

echo "Autostart configured."
echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. If you haven't already, edit the 'config.ini' file with your API key."
echo "2. Please ensure the Pi is set to 'Desktop Autologin' in raspi-config."
echo "3. Reboot your Raspberry Pi with 'sudo reboot'."
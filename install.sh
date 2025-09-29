#!/bin/bash

echo "--- Starting Full Translator Project Setup ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
echo "[1/4] Updating package list and installing system dependencies..."
sudo apt-get update
# ADDED 'lightdm' to ensure graphical boot can be configured
sudo apt-get install -y portaudio19-dev python3-dev xserver-xorg xinit openbox xserver-xorg-input-all lightdm
echo "System dependencies installed."

# --- Step 2: Install Python Dependencies ---
echo "[2/4] Creating virtual environment and installing packages..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate
echo "Python libraries installed successfully."

# --- Step 3: Create and Enable the systemd Service ---
echo "[3/4] Configuring application to run on boot..."
SERVICE_FILE="/etc/systemd/system/translator.service"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Use a 'here document' to write the service file contents
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Audio Translator Service
After=network-online.target sound.target

[Service]
ExecStart=/usr/bin/xinit $LAUNCHER_PATH
WorkingDirectory=$(pwd)
User=pi
Restart=on-failure
Environment="DISPLAY=:0"

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable translator.service
echo "Service enabled."

# --- Step 4: Verify Boot Configuration ---
echo "[4/4] Verifying boot configuration..."
# B4 is the code for "Boot to Desktop with Autologin"
if raspi-config nonint get_boot_behaviour | grep -q "B4"; then
    echo "Boot configuration is correct (Desktop Autologin)."
else
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!! WARNING: Your Pi is not configured to boot into the GUI. !!"
    echo "!! The translator will NOT start automatically after reboot.    !!"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "To fix this, please run 'sudo raspi-config', then go to:"
    echo "'System Options' -> 'Boot / Auto Login' -> 'Desktop Autologin'"
    echo "Then reboot your Pi."
fi

echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. Edit the 'config.ini' file to add your API key."
echo "2. Check for any warnings above, then reboot with 'sudo reboot'."
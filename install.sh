#!/bin/bash

echo "--- Starting Full Translator Project Setup ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
echo "[1/4] Updating package list and installing system dependencies..."
sudo apt-get update
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

# --- Step 3: Create the systemd Service File ---
echo "[3/4] Creating systemd service for autostart..."
SERVICE_FILE="/etc/systemd/system/translator.service"
LAUNCHER_PATH="$(pwd)/launcher.sh"

# Use a 'here document' to write the service file contents
# --- THIS BLOCK CONTAINS THE FIX ---
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Audio Translator Service
After=network-online.target sound.target

[Service]
# FIX: Use 'su' to run the entire graphical session as the 'pi' user
ExecStart=/bin/su - pi -c "/usr/bin/xinit $LAUNCHER_PATH"

WorkingDirectory=$(pwd)
User=pi
Restart=on-failure
Environment="DISPLAY=:0"

[Install]
WantedBy=graphical.target
EOF
# --- END OF FIX ---

echo "Service file created."

# --- Step 4: Enable the Service and Configure Boot ---
echo "[4/4] Enabling service and configuring boot..."
sudo systemctl daemon-reload
sudo systemctl enable translator.service

# B4 is the code for "Boot to Desktop with Autologin"
if raspi-config nonint get_boot_behaviour | grep -q "B4"; then
    echo "Boot configuration is correct (Desktop Autologin)."
else
    echo "Setting boot configuration to Desktop Autologin..."
    sudo raspi-config nonint do_boot_behaviour B4
fi

echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. Edit the 'config.ini' file to add your API key."
echo "2. Reboot your Raspberry Pi with 'sudo reboot'."
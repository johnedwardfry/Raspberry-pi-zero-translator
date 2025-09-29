#!/bin/bash

echo "--- Starting Full Translator Project Setup (Kiosk Mode) ---"
cd "$(dirname "$0")"

# --- Step 1: Install All System Dependencies ---
echo "[1/4] Installing system dependencies (GUI, audio, login manager)..."
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
echo "Python libraries installed."

# --- Step 3: Create the Kiosk Session ---
echo "[3/4] Creating custom graphical session for the translator..."

# Create a script that lightdm will run
SESSION_SCRIPT="/usr/local/bin/translator-session"
LAUNCHER_PATH="$(pwd)/launcher.sh"

sudo tee "$SESSION_SCRIPT" > /dev/null <<EOF
#!/bin/bash
# Run the application launcher
$LAUNCHER_PATH
EOF

# Make the session script executable
sudo chmod +x "$SESSION_SCRIPT"

# Create a .desktop file to register the session
DESKTOP_FILE="/usr/share/xsessions/translator.desktop"
sudo tee "$DESKTOP_FILE" > /dev/null <<EOF
[Desktop Entry]
Name=Translator
Comment=Custom session for the audio translator
Exec=/usr/local/bin/translator-session
Type=Application
EOF

echo "Custom session created."

# --- Step 4: Configure LightDM to Autologin to the Kiosk Session ---
echo "[4/4] Configuring LightDM for automatic login..."
CONF_DIR="/etc/lightdm/lightdm.conf.d"
CONF_FILE="$CONF_DIR/60-autologin.conf"

# Create the directory if it doesn't exist
sudo mkdir -p "$CONF_DIR"

# Create the configuration file
sudo tee "$CONF_FILE" > /dev/null <<EOF
[Seat:*]
autologin-user=pi
autologin-session=translator
EOF

echo "Autologin configured."
echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. Edit the 'config.ini' file to add your API key."
echo "2. Reboot your Raspberry Pi with 'sudo reboot'."
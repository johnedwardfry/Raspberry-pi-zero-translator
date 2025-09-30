#!/bin/bash
set -e

echo "--- Starting Full Translator Project Setup (Kiosk Mode) ---"
cd "$(dirname "$0")"

# --- Step 1: Install System Dependencies ---
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

# --- THIS BLOCK CONTAINS THE FIX ---
# We now create a more robust session that starts openbox first.
SESSION_SCRIPT="/usr/local/bin/translator-session"
LAUNCHER_PATH="$(pwd)/launcher.sh"

sudo tee "$SESSION_SCRIPT" > /dev/null <<EOF
#!/bin/bash
# Start the window manager in the background
openbox &
# Run our application launcher in the foreground
$LAUNCHER_PATH
EOF
# --- END OF FIX ---

sudo chmod +x "$SESSION_SCRIPT"

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
sudo sed -i 's/^#?autologin-user=.*/autologin-user=pi/' /etc/lightdm/lightdm.conf
sudo sed -i 's/^#?autologin-session=.*/autologin-session=translator/' /etc/lightdm/lightdm.conf
echo "Autologin configured."
echo ""
echo "--- ✅ Installation Complete ---"
echo "Next steps:"
echo "1. If you haven't already, edit the 'config.ini' file to add your API key."
echo "2. Reboot your Raspberry Pi with 'sudo reboot'."
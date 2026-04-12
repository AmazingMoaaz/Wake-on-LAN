#!/usr/bin/env bash
set -euo pipefail

# Wake-on-LAN Monitor — Proxmox/Debian installer
# Installs the script as a systemd service

APP_NAME="wol-monitor"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Preflight checks ---
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)."
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "📦 Installing python3..."
    apt-get update -qq && apt-get install -y -qq python3 >/dev/null
fi

# --- Install application files ---
echo "📂 Installing to ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
cp "${SCRIPT_DIR}/main.py" "${INSTALL_DIR}/main.py"
cp "${SCRIPT_DIR}/config.json" "${INSTALL_DIR}/config.json"
chmod 644 "${INSTALL_DIR}/main.py" "${INSTALL_DIR}/config.json"

# --- Create systemd unit ---
echo "⚙️  Creating systemd service..."
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Wake-on-LAN Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/main.py
WorkingDirectory=${INSTALL_DIR}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${APP_NAME}

[Install]
WantedBy=multi-user.target
EOF

# --- Enable and start ---
echo "🚀 Enabling and starting ${APP_NAME} service..."
systemctl daemon-reload
systemctl enable "${APP_NAME}.service"
systemctl start "${APP_NAME}.service"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Useful commands:"
echo "  systemctl status ${APP_NAME}     # Check service status"
echo "  journalctl -u ${APP_NAME} -f     # Follow live logs"
echo "  systemctl restart ${APP_NAME}    # Restart service"
echo "  systemctl stop ${APP_NAME}       # Stop service"
echo ""
echo "Config file: ${INSTALL_DIR}/config.json"
echo "Edit it and run: systemctl restart ${APP_NAME}"

## Wake-on-LAN Monitor

A small monitor that pings your target and sends a Wake-on-LAN (WOL) magic packet when the host is down but the network is up. Works on Windows and Linux. Configuration is via environment variables or a `.env` file placed next to `main.py`.

### File structure
- `main.py` — monitor script
- `.env` — your local config (not committed)
- `env.example` — template you can copy from

### Configuration (.env)
Copy `env.example` to `.env` and adjust values:

```
# Required
WOL_SERVER_IP=192.168.1.3
WOL_SERVER_MAC=7c:05:69:55:52:d2
NETWORK_CHECK_HOST=192.168.1.1

# Optional
BROADCAST_IP=192.168.1.255
WOL_PORT=9
PING_TIMEOUT_MS=1000
CHECK_INTERVAL_SEC=30
WOL_COOLDOWN_SEC=300
```

### Run locally
```
python3 main.py
```

### Ubuntu service setup
1) Place files
```
sudo mkdir -p /opt/wol-monitor
sudo cp main.py /opt/wol-monitor/main.py
sudo cp .env /opt/wol-monitor/.env
```

2) Optional service user
```
sudo useradd -r -s /usr/sbin/nologin wolmon || true
sudo chown -R wolmon:wolmon /opt/wol-monitor
```

3) systemd unit
```
sudo tee /etc/systemd/system/wol-monitor.service >/dev/null << 'EOF'
[Unit]
Description=Wake-on-LAN Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=wolmon
WorkingDirectory=/opt/wol-monitor
EnvironmentFile=/opt/wol-monitor/.env
ExecStart=/usr/bin/python3 /opt/wol-monitor/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
```

4) Enable and watch logs
```
sudo systemctl daemon-reload
sudo systemctl enable --now wol-monitor.service
sudo journalctl -u wol-monitor.service -f
```

### Notes
- Enable WoL in target BIOS/UEFI and NIC. If target is Windows, disable Fast Startup.
- If your network is not /24, set `BROADCAST_IP` to the correct subnet broadcast.
- Tune `CHECK_INTERVAL_SEC`, `WOL_COOLDOWN_SEC`, and `PING_TIMEOUT_MS` for your environment.

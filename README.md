# Wake-on-LAN Monitor

Automatically wakes up your server when it goes offline. Works on Windows and Linux.

## Quick Start

1. **Edit `config.json`** with your server details
2. **Run:** `python3 main.py`

That's it! The script will keep monitoring and wake your server when needed.

---

## Configuration

Edit `config.json` with your settings:

```json
{
  "wol_server_ip": "10.10.1.3",
  "wol_server_mac": "7c:05:69:55:52:d2",
  "network_check_host": "10.10.1.1",
  "broadcast_ip": "10.10.1.255",
  "wol_port": 9,
  "ping_timeout_ms": 1000,
  "check_interval_sec": 30,
  "wol_cooldown_sec": 300
}
```

### What Each Setting Does:

| Setting | What It Is | Example |
|---------|-----------|---------|
| `wol_server_ip` | Your server's IP address | `10.10.1.3` |
| `wol_server_mac` | Your server's MAC address | `7c:05:69:55:52:d2` |
| `network_check_host` | Test IP (usually your router) | `10.10.1.1` |
| `broadcast_ip` | Your network's broadcast IP | `10.10.1.255` |
| `wol_port` | WOL port (leave as 9) | `9` |
| `ping_timeout_ms` | How long to wait for ping | `1000` |
| `check_interval_sec` | Time between checks | `30` |
| `wol_cooldown_sec` | Wait time between wake attempts | `300` |

**All fields are required!**

---

## How to Find Your Settings

**MAC Address:**
- Windows: Open CMD → type `ipconfig /all` → find "Physical Address"
- Linux: Open terminal → type `ip link` → look for your network card

**Broadcast IP:**
- For 10.10.1.x network: `10.10.1.255`
- For 192.168.1.x network: `192.168.1.255`
- For 192.168.0.x network: `192.168.0.255`
- Check your router's IP range if unsure

## Run as Linux Service (Optional)

Want it to run automatically? Follow these steps:

### Step 1: Copy Files
```bash
sudo mkdir -p /opt/wol-monitor
sudo cp main.py /opt/wol-monitor/
sudo cp config.json /opt/wol-monitor/
```

### Step 2: Create Service
```bash
sudo tee /etc/systemd/system/wol-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Wake-on-LAN Monitor
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/wol-monitor
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### Step 3: Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wol-monitor.service
```

### Step 4: Check Logs
```bash
sudo journalctl -u wol-monitor.service -f
```

---

## Important Notes

### On Your Server (the one being woken up):
- ✅ Enable Wake-on-LAN in BIOS/UEFI
- ✅ Enable Wake-on-LAN on your network card
- ✅ If Windows: Disable "Fast Startup" in Power Options

### Troubleshooting:
- Script won't start? Check that `config.json` exists and has all fields filled
- Server won't wake? Make sure it's plugged into power and WOL is enabled in BIOS
- Wrong broadcast IP? Use `.255` at the end of your network range (e.g., `10.10.1.255` for 10.10.1.x network)

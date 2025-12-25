import socket
import subprocess
import platform
import time
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def create_magic_packet(mac):
    """Create a Wake-on-LAN magic packet from a MAC address."""
    mac = mac.replace(":", "").replace("-", "").lower()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address format: {mac}")
    return b'\xff' * 6 + bytes.fromhex(mac) * 16

def send_magic_packet(mac, broadcast, port):
    """Send the Wake-on-LAN magic packet."""
    packet = create_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(packet, (broadcast, port))
    print(f"✅ Magic packet sent to {mac} via {broadcast}:{port}")


def is_host_up(host, timeout_ms):
    """Return True if host responds to a single ping within timeout."""
    system = platform.system().lower()
    try:
        if system == "windows":
            # -n 1 one echo request, -w timeout in ms
            result = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), host],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # -c 1 one echo request, -W timeout in seconds
            timeout_s = max(1, int(round(timeout_ms / 1000)))
            result = subprocess.run(["ping", "-c", "1", "-W", str(timeout_s), host],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def monitor_and_wake(
    wol_server_ip,
    wol_server_mac,
    network_check_host,
    broadcast_ip,
    wol_port,
    ping_timeout_ms,
    check_interval_sec,
    wol_cooldown_sec,
):
    """Continuously monitor servers and send WOL when appropriate."""
    last_wol_sent_at = None
    prev_wol_up = None
    print(f"{now_str()} ▶️  Starting monitor: WOL target={wol_server_ip} ({wol_server_mac}), network check={network_check_host}")
    while True:
        network_up = is_host_up(network_check_host, ping_timeout_ms)
        wol_up = is_host_up(wol_server_ip, ping_timeout_ms)

        if prev_wol_up is None or wol_up != prev_wol_up:
            state = "UP" if wol_up else "DOWN"
            print(f"{now_str()} ℹ️  WOL server state change: {wol_server_ip} is {state}")
            prev_wol_up = wol_up

        if not wol_up:
            if not network_up:
                # Likely outage; skip WOL to avoid spamming during power/network loss
                print(f"{now_str()} ⚠️  Network check host {network_check_host} unreachable. Skipping WOL.")
            else:
                cooldown_ok = (
                    last_wol_sent_at is None
                    or datetime.now() - last_wol_sent_at >= timedelta(seconds=wol_cooldown_sec)
                )
                if cooldown_ok:
                    print(f"{now_str()} 🚀 WOL conditions met. Sending magic packet to {wol_server_mac}...")
                    send_magic_packet(wol_server_mac, broadcast=broadcast_ip, port=wol_port)
                    last_wol_sent_at = datetime.now()
                else:
                    remaining = timedelta(seconds=wol_cooldown_sec) - (datetime.now() - last_wol_sent_at)
                    remaining_s = max(0, int(remaining.total_seconds()))
                    print(f"{now_str()} ⏳ Waiting for cooldown ({remaining_s}s) before sending WOL again.")

        time.sleep(check_interval_sec)

def load_config(config_path: Path) -> dict:
    """Load and validate configuration from JSON file."""
    if not config_path.exists():
        print(f"❌ Error: Configuration file not found: {config_path}")
        print(f"ℹ️  Please create a config.json file with the required settings.")
        sys.exit(1)
    
    try:
        with open(config_path, "r", encoding="utf-8") as fp:
            config = json.load(fp)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: Failed to read configuration file: {e}")
        sys.exit(1)
    
    # Validate all required fields
    required_fields = [
        "wol_server_ip",
        "wol_server_mac",
        "network_check_host",
        "broadcast_ip",
        "wol_port",
        "ping_timeout_ms",
        "check_interval_sec",
        "wol_cooldown_sec"
    ]
    missing_fields = [field for field in required_fields if field not in config or config[field] == ""]
    
    if missing_fields:
        print(f"❌ Error: Missing required configuration fields: {', '.join(missing_fields)}")
        sys.exit(1)
    
    return config


if __name__ == "__main__":
    # Load configuration from JSON file
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.json"
    
    config = load_config(config_path)
    
    print(f"✅ Configuration loaded successfully from {config_path}")
    print(f"   • WOL Server: {config['wol_server_ip']} ({config['wol_server_mac']})")
    print(f"   • Network Check Host: {config['network_check_host']}")
    print(f"   • Broadcast IP: {config['broadcast_ip']}")
    print(f"   • WOL Port: {config['wol_port']}")
    print(f"   • Check Interval: {config['check_interval_sec']}s")
    print(f"   • WOL Cooldown: {config['wol_cooldown_sec']}s")
    print()
    
    monitor_and_wake(
        wol_server_ip=config["wol_server_ip"],
        wol_server_mac=config["wol_server_mac"],
        network_check_host=config["network_check_host"],
        broadcast_ip=config["broadcast_ip"],
        wol_port=config["wol_port"],
        ping_timeout_ms=config["ping_timeout_ms"],
        check_interval_sec=config["check_interval_sec"],
        wol_cooldown_sec=config["wol_cooldown_sec"],
    )

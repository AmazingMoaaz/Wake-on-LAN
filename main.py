import socket
import subprocess
import platform
import time
import os
from datetime import datetime, timedelta

def create_magic_packet(mac):
    """Create a Wake-on-LAN magic packet from a MAC address."""
    mac = mac.replace(":", "").replace("-", "").lower()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address format: {mac}")
    return b'\xff' * 6 + bytes.fromhex(mac) * 16

def send_magic_packet(mac, broadcast="192.168.1.255", port=9):
    """Send the Wake-on-LAN magic packet."""
    packet = create_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(packet, (broadcast, port))
    print(f"✅ Magic packet sent to {mac} via {broadcast}:{port}")


def is_host_up(host, timeout_ms=1000):
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
    broadcast_ip="192.168.1.255",
    wol_port=9,
    ping_timeout_ms=1000,
    check_interval_sec=30,
    wol_cooldown_sec=300,
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

def load_env_file(dotenv_path: str) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (no external deps)."""
    if not os.path.isfile(dotenv_path):
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as fp:
            for raw_line in fp:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Safe fail; env-only config will still work
        pass


def getenv_str(name: str, default: str | None = None, required: bool = False) -> str | None:
    value = os.environ.get(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise RuntimeError(f"Missing required configuration: {name}")
    return value


def getenv_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


if __name__ == "__main__":
    # Load .env from the script directory if present
    script_dir = os.path.dirname(os.path.abspath(__file__))
    load_env_file(os.path.join(script_dir, ".env"))

    # Required settings
    WOL_SERVER_IP = getenv_str("WOL_SERVER_IP", required=True)
    WOL_SERVER_MAC = getenv_str("WOL_SERVER_MAC", required=True)
    NETWORK_CHECK_HOST = getenv_str("NETWORK_CHECK_HOST", required=True)

    # Optional settings with defaults
    BROADCAST_IP = getenv_str("BROADCAST_IP", "192.168.1.255")
    WOL_PORT = getenv_int("WOL_PORT", 9)
    PING_TIMEOUT_MS = getenv_int("PING_TIMEOUT_MS", 1000)
    CHECK_INTERVAL_SEC = getenv_int("CHECK_INTERVAL_SEC", 30)
    WOL_COOLDOWN_SEC = getenv_int("WOL_COOLDOWN_SEC", 300)

    monitor_and_wake(
        wol_server_ip=WOL_SERVER_IP,
        wol_server_mac=WOL_SERVER_MAC,
        network_check_host=NETWORK_CHECK_HOST,
        broadcast_ip=BROADCAST_IP,
        wol_port=WOL_PORT,
        ping_timeout_ms=PING_TIMEOUT_MS,
        check_interval_sec=CHECK_INTERVAL_SEC,
        wol_cooldown_sec=WOL_COOLDOWN_SEC,
    )

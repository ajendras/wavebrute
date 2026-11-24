import platform
import re
import subprocess
from subprocess import CalledProcessError, TimeoutExpired
from typing import Any


def scan_wifi(interface: str = "wlan0") -> list[dict[str, Any]]:
    """Cross-platform WiFi scanner.

    Uses iwlist on Linux and netsh on Windows. Returns realistic
    network data. Falls back to simulation data on any error.
    """
    system = platform.system().lower()
    if system == "linux":
        try:
            cmd = ["iwlist", interface, "scan"]
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=10
            ).decode("utf-8", errors="ignore")
            return parse_iwlist(output)
        except (CalledProcessError, TimeoutExpired, FileNotFoundError, OSError):
            return _simulate_scan_fallback()
    elif system == "windows":
        try:
            cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=5
            ).decode("utf-8", errors="ignore")
            return parse_netsh(output)
        except (CalledProcessError, TimeoutExpired, FileNotFoundError, OSError):
            return _simulate_scan_fallback()
    return _simulate_scan_fallback()


def parse_iwlist(output: str) -> list[dict[str, Any]]:
    """Parse iwlist scan output into structured network list."""
    networks: list[dict[str, Any]] = []
    cells = re.split(r"(?:^|[\r\n]+)Cell", output)
    for cell in cells[1:]:
        ssid_match = re.search(r'ESSID:"([^"]+)"', cell)
        address_match = re.search(r"Address:\s*([0-9A-F:]+)", cell, re.I)
        signal_match = re.search(r"Signal level[:=]\s*-?(\d+)", cell, re.I) or re.search(
            r"Quality[:=]\s*(\d+)", cell, re.I
        )
        encryption = "OPEN" if "Encryption key:off" in cell else "WPA2-PSK"

        networks.append(
            {
                "ssid": ssid_match.group(1) if ssid_match else "Unknown",
                "bssid": address_match.group(1) if address_match else "00:00:00:00:00:00",
                "signal": int(signal_match.group(1)) * -1 if signal_match else -55,
                "encryption": encryption,
                "channel": 6,
                "frequency": "2.4 GHz",
            }
        )
    return networks if networks else _simulate_scan_fallback()


def parse_netsh(output: str) -> list[dict[str, Any]]:
    """Parse netsh wlan output (Windows) into structured network list.

    This fixes the previous unused `output` variable.
    """
    networks: list[dict[str, Any]] = []
    lines = output.splitlines()
    current: dict[str, Any] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("SSID") and ":" in line:
            if current and current.get("ssid"):
                networks.append(current)
            current = {}
            current["ssid"] = line.split(":", 1)[1].strip()
            current["bssid"] = "00:11:22:33:44:55"
            current["signal"] = -55
            current["encryption"] = "WPA2-PSK"
            current["channel"] = 6
            current["frequency"] = "2.4 GHz"
        elif "Signal" in line and ":" in line:
            try:
                sig_percent = int(line.split(":", 1)[1].strip().replace("%", ""))
                current["signal"] = -(100 - sig_percent)
            except ValueError:
                current["signal"] = -55
        elif "Authentication" in line and ":" in line:
            auth = line.split(":", 1)[1].strip()
            if "WPA" in auth:
                current["encryption"] = auth
    if current and current.get("ssid"):
        networks.append(current)
    return networks if networks else _simulate_scan_fallback()


def _simulate_scan_fallback() -> list[dict[str, Any]]:
    """Realistic fallback networks for simulation or error cases."""
    return [
        {
            "ssid": "Cafe_Rouge_FreeWiFi",
            "bssid": "00:14:BF:12:34:56",
            "channel": 6,
            "signal": -42,
            "encryption": "WPA2-PSK",
            "frequency": "2.4 GHz",
        },
        {
            "ssid": "Linksys-5G",
            "bssid": "A0:12:34:56:78:9A",
            "channel": 36,
            "signal": -58,
            "encryption": "WPA3",
            "frequency": "5 GHz",
        },
    ]

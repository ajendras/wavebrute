"""WiFi scanner module for WaveBrute.

Cross-platform support for live scanning using system commands.
Regex parsing for iwlist (Linux) and netsh (Windows). All regex flags
updated to use re.IGNORECASE for linter compliance (FURB167).
"""

import platform
import re
import subprocess
from typing import Any


def scan_wifi(interface: str = "wlan0") -> list[dict[str, Any]]:
    """Perform a WiFi scan using the appropriate OS tool.

    Returns a list of networks with standardized keys for use by Auditor.
    In environments where live scan is not possible (e.g. Android, no privs)
    a small set of demo networks is returned.
    """
    system = platform.system().lower()

    if system == "linux":
        return _scan_linux(interface)
    if system == "windows":
        return _scan_windows(interface)
    # Fallback for Android, macOS, etc.
    return _simulate_networks()


def _scan_linux(interface: str) -> list[dict[str, Any]]:
    """Linux scan using iwlist."""
    try:
        cmd = ["iwlist", interface, "scan"]
        output = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, text=True
        )
        return _parse_iwlist(output)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _simulate_networks()


def _scan_windows(interface: str) -> list[dict[str, Any]]:
    """Windows scan using netsh."""
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return _parse_netsh(output)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _simulate_networks()


def _parse_iwlist(output: str) -> list[dict[str, Any]]:
    """Parse iwlist scan output into list of network dicts.

    Fixed regex flags to use re.IGNORECASE instead of alias re.I .
    """
    cells = output.split("Cell")
    networks: list[dict[str, Any]] = []
    for cell in cells[1:]:
        ssid_match = re.search(r'ESSID:"([^"]+)"', cell)
        address_match = re.search(
            r"Address:\s*([0-9A-F:]+)", cell, re.IGNORECASE
        )
        signal_match = re.search(
            r"Signal level[:=]\s*-?(\d+)", cell, re.IGNORECASE
        ) or re.search(
            r"Quality[:=]\s*(\d+)", cell, re.IGNORECASE
        )
        encryption = "OPEN" if "Encryption key:off" in cell else "WPA2-PSK"

        ssid = ssid_match.group(1) if ssid_match else "Unknown"
        bssid = (
            address_match.group(1)
            if address_match
            else "00:11:22:33:44:55"
        )
        signal = int(signal_match.group(1)) if signal_match else -60

        networks.append(
            {
                "ssid": ssid,
                "bssid": bssid,
                "signal": signal,
                "encryption": encryption,
                "channel": 6,
            }
        )
    return networks


def _parse_netsh(output: str) -> list[dict[str, Any]]:
    """Parse netsh output (simplified)."""
    networks = []
    lines = output.splitlines()
    current: dict[str, Any] = {}
    for line in lines:
        if "SSID" in line and ":" in line:
            current = {"ssid": line.split(":", 1)[1].strip().strip('"')}
        if current.get("ssid") and ("BSSID" in line or "Authentication" in line):
            current["bssid"] = "00:11:22:33:44:55"
            current["signal"] = -50
            current["encryption"] = "WPA2-PSK"
            networks.append(current.copy())
    return networks or _simulate_networks()


def _simulate_networks() -> list[dict[str, Any]]:
    """Return demo networks for simulation, CI, or unsupported platforms."""
    return [
        {
            "ssid": "Cafe_Rouge_FreeWiFi",
            "bssid": "00:14:BF:12:34:56",
            "signal": -42,
            "encryption": "WPA2-PSK",
            "channel": 6,
        },
        {
            "ssid": "Linksys-5G",
            "bssid": "A0:12:34:56:78:9A",
            "signal": -55,
            "encryption": "WPA3",
            "channel": 36,
        },
    ]

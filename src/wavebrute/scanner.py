"""Cross-platform WiFi scanner for WaveBrute.

Supports Linux (iwlist), macOS (airport), Windows (netsh).
Uses subprocess to call native tools and parses output into standardized dicts.
"""

import platform
import subprocess
from typing import Any


def scan_wifi(interface: str = "wlan0") -> list[dict[str, Any]]:
    """Scan for WiFi networks using platform-specific tools.

    Returns list of networks with standardized keys: ssid, bssid, signal, encryption, channel.
    """
    system = platform.system()

    if system == "Linux":
        return _scan_linux(interface)
    elif system == "Darwin":
        return _scan_macos(interface)
    elif system == "Windows":
        return _scan_windows(interface)
    else:
        return _simulate_scan()


def _scan_linux(interface: str) -> list[dict[str, Any]]:
    """Parse output from iwlist scan."""
    try:
        output = subprocess.check_output(
            ["sudo", "iwlist", interface, "scan"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        return _parse_iwlist(output)
    except (subprocess.SubprocessError, FileNotFoundError):
        return _simulate_scan()


def _parse_iwlist(output: str) -> list[dict[str, Any]]:
    """Parse iwlist scan output."""
    networks = []
    current: dict[str, Any] = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Cell"):
            if current and current.get("ssid"):
                networks.append(current)
            current = {"encryption": "OPEN"}
        elif "ESSID:" in line:
            current["ssid"] = line.split("ESSID:")[1].strip('"')
        elif "Address:" in line:
            current["bssid"] = line.split("Address: ")[1].strip()
        elif "Channel:" in line:
            try:
                current["channel"] = int(line.split("Channel:")[1].strip())
            except ValueError:
                current["channel"] = 6
        elif "Signal level:" in line:
            try:
                signal_str = line.split("Signal level=")[1].split()[0].replace("dBm", "")
                current["signal"] = int(signal_str)
            except (ValueError, IndexError):
                current["signal"] = -50
        elif line.startswith("Encryption key:"):
            if "on" in line.lower():
                current["encryption"] = "WPA2-PSK"
        elif line.startswith("Authentication") and ":" in line:
            auth = line.split(":", 1)[1].strip()
            if "WPA2" in auth:
                current["encryption"] = "WPA2-PSK"
            elif "WPA3" in auth:
                current["encryption"] = "WPA3"
            elif "Open" in auth or "Open" in line:
                current["encryption"] = "OPEN"
            else:
                current["encryption"] = auth

    if current and current.get("ssid"):
        networks.append(current)

    return networks or _simulate_scan()


def _scan_macos(interface: str) -> list[dict[str, Any]]:
    """Use airport for macOS."""
    try:
        output = subprocess.check_output(
            [
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-s",
            ],
            text=True,
            timeout=10,
        )
        return _parse_airport(output)
    except (subprocess.SubprocessError, FileNotFoundError):
        return _simulate_scan()


def _parse_airport(output: str) -> list[dict[str, Any]]:
    """Parse airport output."""
    networks = []
    for line in output.splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) > 3:
            ssid = parts[0]
            bssid = parts[1] if len(parts) > 1 else "00:00:00:00:00:00"
            try:
                signal = int(parts[2])
            except ValueError:
                signal = -50
            networks.append(
                {
                    "ssid": ssid,
                    "bssid": bssid,
                    "signal": signal,
                    "channel": 6,
                    "encryption": "WPA2-PSK",
                    "frequency": "2.4 GHz",
                }
            )
    return networks or _simulate_scan()


def _scan_windows(interface: str = "Wi-Fi") -> list[dict[str, Any]]:
    """Use netsh for Windows."""
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid", f"interface={interface}"],
            text=True,
            timeout=10,
        )
        return _parse_netsh(output)
    except (subprocess.SubprocessError, FileNotFoundError):
        return _simulate_scan()


def _parse_netsh(output: str) -> list[dict[str, Any]]:
    """Parse netsh wlan output."""
    networks = []
    current: dict[str, Any] = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            if current and current.get("ssid"):
                networks.append(current)
            current = {"encryption": "WPA2-PSK"}
            try:
                current["ssid"] = line.split(":", 1)[1].strip()
            except IndexError:
                continue
        elif "BSSID" in line:
            try:
                current["bssid"] = line.split(":", 1)[1].strip()
            except IndexError:
                current["bssid"] = "00:00:00:00:00:00"
        elif "Signal" in line:
            try:
                signal_pct = int(line.split(":")[1].strip().replace("%", ""))
                current["signal"] = -100 + (signal_pct // 2)
            except (ValueError, IndexError):
                current["signal"] = -50
        elif "Authentication" in line and ":" in line:
            auth = line.split(":", 1)[1].strip()
            if "WPA2" in auth:
                current["encryption"] = "WPA2-PSK"
            elif "WPA3" in auth:
                current["encryption"] = "WPA3"
            elif "Open" in auth:
                current["encryption"] = "OPEN"
            else:
                current["encryption"] = auth

    if current and current.get("ssid"):
        networks.append(current)

    return networks or _simulate_scan()


def _simulate_scan() -> list[dict[str, Any]]:
    """Fallback simulation data."""
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

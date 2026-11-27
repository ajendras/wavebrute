"""Cross-platform WiFi scanner for WaveBrute.

Supports Linux (iwlist), Windows (netsh), and macOS (airport).
The scan_wifi() function is the main entry point used by Auditor.scan().

All parsing functions are private and handle the platform-specific output formats.
Simulation mode is handled in auditor.py; this module only does live scans.
"""

from __future__ import annotations

import platform
import re
import subprocess
from typing import Any


def scan_wifi(interface: str = "wlan0") -> list[dict[str, Any]]:
    """Scan for nearby WiFi networks using platform-specific tools.

    - Linux: uses iwlist (requires root/sudo usually)
    - Windows: uses netsh wlan (no admin needed for basic scan)
    - macOS: uses airport -s (built-in, no extra privileges for scan)

    Returns a list of network dicts with standardized keys:
    ssid, bssid, channel, signal (RSSI), encryption, frequency.

    Args:
        interface: Name of the wireless interface (e.g. wlan0, Wi-Fi, en0).

    Returns:
        List of discovered networks.

    Raises:
        RuntimeError: If the platform-specific command fails or is unavailable.
        NotImplementedError: For unsupported platforms.
    """
    system = platform.system().lower()

    if system == "linux":
        return _scan_linux(interface)
    elif system == "windows":
        return _scan_windows(interface)
    elif system == "darwin":
        return _scan_macos(interface)
    else:
        raise NotImplementedError(
            f"Platform '{platform.system()}' is not supported. "
            "WaveBrute currently supports Linux, Windows, and macOS."
        )


def _scan_linux(interface: str) -> list[dict[str, Any]]:
    """Scan using Linux iwlist command."""
    try:
        cmd = ["iwlist", interface, "scanning"]
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=10
        )
        networks = _parse_iwlist(output)
        return networks
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"iwlist scan failed on {interface}. "
            "Try running with sudo or use simulation_mode=True. "
            f"Error: {exc.output}"
        ) from exc
    except FileNotFoundError:
        raise RuntimeError(
            "iwlist command not found. Install wireless-tools package."
        ) from None


def _scan_windows(interface: str) -> list[dict[str, Any]]:
    """Scan using Windows netsh command."""
    try:
        cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=10
        )
        networks = _parse_netsh(output)
        return networks
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"netsh scan failed: {exc}") from exc
    except FileNotFoundError:
        raise RuntimeError("netsh command not available.") from None


def _scan_macos(interface: str = "en0") -> list[dict[str, Any]]:
    """Scan using macOS airport utility (new)."""
    airport_path = (
        "/System/Library/PrivateFrameworks/"
        "Apple80211.framework/Versions/Current/Resources/airport"
    )
    try:
        cmd = [airport_path]
        iface = interface.strip() if interface else "en0"
        if iface and iface not in ("", "en0"):
            cmd.append(iface)
        cmd.append("-s")
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=10
        )
        networks = _parse_airport(output)
        return networks
    except FileNotFoundError:
        raise RuntimeError(
            "airport utility not found. This is unexpected on macOS."
        ) from None
    except subprocess.CalledProcessError as exc:
        err = exc.output if isinstance(exc.output, str) else exc.output.decode()
        raise RuntimeError(f"airport scan failed: {err}") from exc


def _parse_iwlist(output: str) -> list[dict[str, Any]]:
    """Parse output from Linux iwlist scanning."""
    networks: list[dict[str, Any]] = []
    cells = re.split(r"\s*Cell \d+ - ", output)

    for cell in cells[1:]:
        ssid_match = re.search(r'ESSID:"([^"]+)"', cell)
        address_match = re.search(r"Address: ([0-9A-F:]+)", cell)
        signal_match = re.search(r"Signal level=([-\d]+)", cell)
        channel_match = re.search(r"Channel:(\d+)", cell)

        if not ssid_match:
            continue

        ssid = ssid_match.group(1)
        bssid = address_match.group(1) if address_match else "00:00:00:00:00:00"
        signal = int(signal_match.group(1)) if signal_match else -50
        channel = int(channel_match.group(1)) if channel_match else 1

        encryption = "OPEN"
        if "WPA" in cell or "WEP" in cell:
            if "WPA3" in cell:
                encryption = "WPA3"
            elif "WPA2" in cell:
                encryption = "WPA2-PSK"
            elif "WPA" in cell:
                encryption = "WPA-PSK"
            else:
                encryption = "WEP"

        frequency = "2.4 GHz" if channel <= 14 else "5 GHz"

        networks.append(
            {
                "ssid": ssid,
                "bssid": bssid,
                "channel": channel,
                "signal": signal,
                "encryption": encryption,
                "frequency": frequency,
            }
        )

    return networks


def _parse_netsh(output: str) -> list[dict[str, Any]]:
    """Parse output from Windows netsh wlan show networks."""
    networks: list[dict[str, Any]] = []
    lines = output.splitlines()
    current: dict[str, Any] = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("SSID"):
            if current and current.get("ssid"):
                networks.append(current)
            current = {"ssid": line.split(":", 1)[1].strip() if ":" in line else line}
        elif line.startswith("BSSID"):
            if ":" in line:
                current["bssid"] = line.split(":", 1)[1].strip()
        elif line.startswith("Signal"):
            if ":" in line:
                signal_str = line.split(":", 1)[1].strip().replace("%", "")
                try:
                    current["signal"] = -int((100 - int(signal_str)) / 2)
                except ValueError:
                    current["signal"] = -50
        elif line.startswith("Authentication"):
            if ":" in line:
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

    # Fill defaults for missing fields
    for net in networks:
        net.setdefault("bssid", "00:00:00:00:00:00")
        net.setdefault("channel", 1)
        net.setdefault("signal", -50)
        net.setdefault("encryption", "WPA2")
        net.setdefault("frequency", "2.4 GHz")

    return networks


def _parse_airport(output: str) -> list[dict[str, Any]]:
    """Parse output from macOS airport -s command."""
    networks: list[dict[str, Any]] = []
    lines = output.splitlines()

    for line in lines[1:]:
        if not line.strip() or "SSID" in line and "BSSID" in line:
            continue

        # SSID may contain spaces; BSSID is always a MAC; RSSI and channel follow
        match = re.match(
            r"\s*(?P<ssid>.+?)\s+(?P<bssid>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})\s+"
            r"(?P<rssi>-\d+)\s+(?P<channel>\d+)(?:,\d+)?",
            line,
        )
        if not match:
            continue

        ssid = match.group("ssid").strip()
        bssid = match.group("bssid")
        rssi = int(match.group("rssi"))
        channel = int(match.group("channel").split(",")[0])

        # Security info is at the end of the line
        remainder = line[match.end():].strip() if match.end() else ""
        security = remainder.split()[0] if remainder else ""

        encryption = "OPEN"
        sec_upper = security.upper()
        if any(x in sec_upper for x in ("WPA", "WEP", "RSN")):
            if "WPA3" in sec_upper or "RSN" in sec_upper:
                encryption = "WPA3"
            elif "WPA2" in sec_upper:
                encryption = "WPA2-PSK"
            elif "WPA" in sec_upper:
                encryption = "WPA-PSK"
            elif "WEP" in sec_upper:
                encryption = "WEP"

        frequency = "5 GHz" if channel > 14 else "2.4 GHz"

        networks.append(
            {
                "ssid": ssid,
                "bssid": bssid,
                "channel": channel,
                "signal": rssi,
                "encryption": encryption,
                "frequency": frequency,
            }
        )

    return networks


# Backward compatibility alias used in documentation
parse_iwlist = _parse_iwlist

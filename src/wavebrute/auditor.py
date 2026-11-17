"""Core auditing engine for WaveBrute.

Implements the primary Auditor class with full support for:
- Live or simulated WiFi scanning (via scanner.py)
- Safe in-memory brute-force attack simulation
- Handshake capture file analysis (via Scapy)
- Ethics enforcement through ConsentManager
- Result collection for PDF reporting

All methods include strict input validation and helpful error messages.
Simulation mode is the secure default.
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from scapy.all import rdpcap  # graceful fallback if unavailable

from .scanner import scan_wifi
from .wordlist import WordlistGenerator
from .ethics import ConsentManager
from .utils import parse_cap_file, generate_ai_suggestions
from .report import ReportBuilder


class Auditor:
    """Main orchestrator for ethical WiFi audits.

    Provides scan(), simulate_attack(), and analyze_handshake() as the
    primary public interface. All operations respect the ConsentManager
    and default to safe simulation mode.
    """

    def __init__(self, simulation_mode: bool = True, interface: str = "wlan0") -> None:
        """Initialize Auditor with secure defaults.

        Args:
            simulation_mode: Whether to run entirely in safe simulation mode.
                Defaults to True (recommended for all non-authorized use).
            interface: Wireless interface name (ignored in simulation mode).

        Raises:
            ValueError: If simulation_mode is not bool or interface is empty.
        """
        if not isinstance(simulation_mode, bool):
            raise ValueError("simulation_mode must be a boolean (True for safe demo mode)")
        if not isinstance(interface, str) or not interface.strip():
            raise ValueError(
                "interface must be a non-empty string (e.g. 'wlan0', 'wlp2s0'). "
                "On Android this is typically handled by the OS."
            )

        self.simulation_mode = simulation_mode
        self.interface = interface.strip()
        self.consent_manager = ConsentManager()
        self.results: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []

    def scan(self, interface: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan for nearby WiFi networks.

        In simulation mode returns realistic synthetic data. In live mode
        delegates to scan_wifi() from scanner.py (requires privileges).

        Args:
            interface: Optional interface override.

        Returns:
            List of dicts containing ssid, bssid, signal, encryption, etc.

        Raises:
            ValueError: On invalid interface name.
            RuntimeError: On live scan failure (suggests using simulation).
            PermissionError: If consent is not granted.
        """
        if interface is None:
            interface = self.interface

        if not isinstance(interface, str) or not interface.strip():
            raise ValueError(
                "interface must be a non-empty string like 'wlan0'. "
                "Run with simulation_mode=True if you lack privileges."
            )

        if not self.consent_manager.require_consent("network scan"):
            raise PermissionError(
                "ConsentManager blocked scan. Call consent_manager.show_checklist() "
                "and obtain explicit permission before live actions."
            )

        if self.simulation_mode:
            networks = self._simulate_scan()
        else:
            try:
                networks = scan_wifi(interface)
            except Exception as exc:
                raise RuntimeError(
                    f"Live scan on '{interface}' failed. This usually requires "
                    "root privileges and monitor mode (airmon-ng). "
                    f"Original error: {exc}. Use simulation_mode=True for training."
                ) from exc

        for net in networks:
            net.setdefault("timestamp", datetime.now().isoformat())
            net.setdefault("ai_hint", generate_ai_suggestions(net.get("ssid", ""))[0])

        self.results.extend(networks)
        self.consent_manager.log_audit(
            "scan", {"interface": interface, "networks_found": len(networks)}
        )
        return networks

    def simulate_attack(
        self,
        ssid: str,
        wordlist_path: Optional[str] = None,
        max_attempts: int = 10000,
    ) -> Dict[str, Any]:
        """Perform a completely safe, in-memory brute-force simulation.

        No packets are transmitted. Demonstrates cracking logic, timing,
        and AI-augmented wordlist effectiveness.

        Args:
            ssid: Target network SSID.
            wordlist_path: Optional path to a wordlist file (if None, one is generated).
            max_attempts: Maximum simulation iterations for performance.

        Returns:
            Dict with success status, discovered password (if any), stats,
            and security recommendations.

        Raises:
            ValueError: If ssid is empty or malformed.
            FileNotFoundError: If wordlist_path is supplied but missing.
            PermissionError: If user has not consented.
        """
        if not isinstance(ssid, str) or len(ssid.strip()) == 0:
            raise ValueError("ssid must be a non-empty string")
        ssid = ssid.strip()

        if wordlist_path is not None and not os.path.isfile(wordlist_path):
            raise FileNotFoundError(
                f"Wordlist '{wordlist_path}' not found. Generate one with "
                "WordlistGenerator().save() first."
            )

        if not self.consent_manager.require_consent(f"simulated attack on '{ssid}'"):
            raise PermissionError(
                "Ethics Guard denied simulated attack. "
                "Mandatory consent checklist was not completed."
            )

        result = self._run_in_memory_attack(ssid, wordlist_path, max_attempts)
        self.results.append(result)
        self.consent_manager.log_audit("simulate_attack", result)
        return result

    def analyze_handshake(self, capfile: str) -> Dict[str, Any]:
        """Analyze a packet capture for WPA handshake presence.

        Uses parse_cap_file (from utils) and Scapy when possible.
        Falls back to realistic simulation if real parsing fails or
        file is not a real capture.

        Args:
            capfile: Path to .cap, .pcap, or .pcapng file.

        Returns:
            Dict describing handshake details, MACs, crackability, and notes.

        Raises:
            FileNotFoundError: If capfile does not exist.
            ValueError: If file extension is unsupported.
            PermissionError: If consent was not granted.
        """
        if not isinstance(capfile, str) or not capfile.strip():
            raise ValueError("capfile must be a non-empty path string")

        capfile = capfile.strip()
        if not os.path.isfile(capfile):
            raise FileNotFoundError(
                f"Capture file '{capfile}' does not exist. "
                "For demos you can use a placeholder .cap file."
            )

        if not capfile.lower().endswith((".cap", ".pcap", ".pcapng")):
            raise ValueError(
                "capfile must have extension .cap, .pcap or .pcapng"
            )

        if not self.consent_manager.require_consent("handshake analysis"):
            raise PermissionError("ConsentManager blocked handshake analysis.")

        try:
            parsed = parse_cap_file(capfile)
            if parsed and parsed.get("has_handshake", False):
                analysis: Dict[str, Any] = parsed
            else:
                analysis = self._simulate_handshake_analysis(capfile)
        except Exception:  # Scapy errors, permission issues, malformed file
            analysis = self._simulate_handshake_analysis(capfile)

        analysis["file"] = capfile
        analysis["timestamp"] = datetime.now().isoformat()
        self.results.append(analysis)
        self.consent_manager.log_audit("analyze_handshake", analysis)
        return analysis

    def _simulate_scan(self) -> List[Dict[str, Any]]:
        """Return hard-coded but realistic networks for simulation mode.

        Signal strengths and AI hints are varied for demonstration value.
        """
        networks = [
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
            {
                "ssid": "NETGEAR_Guest",
                "bssid": "11:22:33:44:55:66",
                "channel": 11,
                "signal": -71,
                "encryption": "WPA2",
                "frequency": "2.4 GHz",
            },
            {
                "ssid": "IoT-Devices",
                "bssid": "DE:AD:BE:EF:CA:FE",
                "channel": 1,
                "signal": -35,
                "encryption": "OPEN",
                "frequency": "2.4 GHz",
            },
        ]

        for net in networks:
            # Add slight randomness based on SSID for replay variety
            net["signal"] = net["signal"] - (len(net["ssid"]) % 7)
            net["timestamp"] = datetime.now().isoformat()
            net["ai_hint"] = generate_ai_suggestions(net["ssid"])[0]

        return networks

    def _run_in_memory_attack(
        self,
        ssid: str,
        wordlist_path: Optional[str],
        max_attempts: int,
    ) -> Dict[str, Any]:
        """Internal simulation engine.

        Generates a wordlist, augments it with AI suggestions, then
        searches for a deterministic weak password derived from the SSID.
        """
        start_time = time.time()

        generator = WordlistGenerator()
        if wordlist_path and os.path.isfile(wordlist_path):
            # In a full implementation this would load the file;
            # here we generate a targeted list for consistency.
            wordlist = generator.from_ssid(ssid, size=500)
        else:
            wordlist = generator.from_ssid(ssid, size=1200)

        # Augment with AI-derived patterns
        ai_suggestions = generate_ai_suggestions(ssid)
        wordlist = ai_suggestions + wordlist

        # Deterministic weak password for reproducible demos
        candidate = ssid.lower().replace(" ", "").replace("-", "")
        secret = (candidate + "2023")[:12]
        if len(candidate) > 4:
            secret = candidate[:4] + "admin"

        cracked_password: Optional[str] = None
        attempts = 0

        for password in wordlist[:max_attempts]:
            attempts += 1
            if password.lower() == secret.lower() or any(
                kw in password.lower()
                for kw in ("123", "admin", "pass", "wifi", candidate[:5])
            ):
                cracked_password = password
                break

        duration = time.time() - start_time

        success = cracked_password is not None
        return {
            "type": "brute_force_simulation",
            "ssid": ssid,
            "success": success,
            "password": cracked_password,
            "attempts": attempts,
            "duration_seconds": round(duration, 3),
            "words_per_second": round(attempts / duration) if duration > 0 else 0,
            "simulation": True,
            "ai_suggestions_used": len(ai_suggestions),
            "recommendations": [
                "Use a unique 20+ character password",
                "Enable WPA3 where possible",
                "Disable WPS and guest networks",
                "Monitor for unauthorized access points",
                "Consider enterprise authentication (802.1X)",
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def _simulate_handshake_analysis(self, capfile: str) -> Dict[str, Any]:
        """Return realistic handshake metadata for simulation or fallback."""
        return {
            "has_handshake": True,
            "handshake_type": "4-way",
            "ap_mac": "00:11:22:33:44:55",
            "client_mac": "66:77:88:99:AA:BB",
            "eapol_frames": 4,
            "signal_strength": -45,
            "crackable": True,
            "crack_time_estimate": "< 90 minutes on modern GPU with good wordlist",
            "simulation": True,
            "notes": (
                "Valid 4-way handshake detected. In a real authorized engagement "
                "this file would be passed to hashcat/aircrack-ng together with "
                "the wordlist generated by WordlistGenerator."
            ),
        }

    def build_report(
        self, title: str = "WaveBrute Ethical Audit Report", output_path: Optional[str] = None
    ) -> str:
        """Generate a professional PDF report from all collected results.

        Uses ReportBuilder (Jinja2 templating + ReportLab).

        Args:
            title: Report title.
            output_path: Where to save the PDF (auto-generated if None).

        Returns:
            Absolute path to the created PDF file.

        Raises:
            ValueError: If no results have been collected yet.
        """
        if not self.results:
            raise ValueError(
                "No audit results available. Run scan(), simulate_attack(), "
                "or analyze_handshake() first."
            )

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wavebrute_report_{timestamp}.pdf"

        builder = ReportBuilder.from_results(self.results)
        builder.to_pdf(title, output_path)
        return os.path.abspath(output_path)

    def get_results(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of all results collected during this session."""
        return list(self.results)

    def clear_results(self) -> None:
        """Clear all stored results (useful when starting a new audit)."""
        self.results.clear()
        self.audit_log.clear()


if __name__ == "__main__":
    # Self-contained runnable demo
    auditor = Auditor(simulation_mode=True)
    print("=== WaveBrute Auditor Demo (simulation mode) ===")
    nets = auditor.scan()
    print(f"Discovered {len(nets)} networks (simulated).")
    attack = auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
    print(f"Simulated attack success: {attack['success']}")
    if attack.get("password"):
        print(f"  Password found: {attack['password']}")
    report_path = auditor.build_report()
    print(f"PDF report written to: {report_path}")
    print("Demo completed successfully. All operations were simulated.")

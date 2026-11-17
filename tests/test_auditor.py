"""Tests for the Auditor class.

Comprehensive test suite covering initialization, simulation paths,
consent handling, handshake analysis (including fallback for missing files),
reporting, and error conditions. All tests run in safe simulation mode.
"""

import os
from unittest.mock import patch
import pytest

from wavebrute.auditor import Auditor
from wavebrute.ethics import ConsentManager


@pytest.fixture
def auditor() -> Auditor:
    """Auditor fixture in safe simulation mode (consent auto-approved via action keywords)."""
    return Auditor(simulation_mode=True, interface="wlan0")


def test_initialization() -> None:
    """Test Auditor init validation and defaults."""
    with pytest.raises(ValueError, match="boolean"):
        Auditor(simulation_mode="notbool")
    with pytest.raises(ValueError, match="non-empty string"):
        Auditor(interface="")

    aud = Auditor(simulation_mode=True)
    assert aud.simulation_mode is True
    assert aud.interface == "wlan0"
    assert len(aud.get_results()) == 0


def test_simulate_scan(auditor: Auditor) -> None:
    """Test that scan in simulation mode returns realistic synthetic data."""
    networks = auditor.scan()
    assert len(networks) == 4
    ssids = {n.get("ssid") for n in networks}
    assert "Cafe_Rouge_FreeWiFi" in ssids
    assert "Linksys-5G" in ssids
    assert all("timestamp" in n and "ai_hint" in n for n in networks)
    assert len(auditor.get_results()) >= 4


def test_analyze_handshake_validation(auditor: Auditor) -> None:
    """Test handshake analysis validation and simulation fallback for missing files.

    Previously raised FileNotFoundError for 'bad.txt'; now falls back to
    simulation as documented in docstring, README, and CLI usage.
    """
    analysis = auditor.analyze_handshake("bad.txt")
    assert analysis["simulation"] is True
    assert analysis["has_handshake"] is True
    assert analysis["file"] == "bad.txt"
    assert "crack_time_estimate" in analysis
    assert "4-way" in analysis.get("handshake_type", "")


def test_build_report(auditor: Auditor, tmp_path) -> None:
    """Test PDF report generation from collected simulation results."""
    auditor.clear_results()
    auditor.scan()
    auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=2000)
    auditor.analyze_handshake("demo.cap")

    report_path = str(tmp_path / "test_audit_report.pdf")
    path = auditor.build_report(title="CI Test Report", output_path=report_path)
    assert os.path.isfile(path)
    assert path.endswith(".pdf")


def test_clear_results(auditor: Auditor) -> None:
    """Clearing results resets session state."""
    auditor.scan()
    auditor.simulate_attack("NETGEAR_Guest")
    assert len(auditor.get_results()) > 0

    auditor.clear_results()
    assert len(auditor.get_results()) == 0


def test_simulate_attack_deterministic(auditor: Auditor) -> None:
    """Test in-memory attack finds deterministic weak password from SSID."""
    result = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=5000)
    assert result["success"] is True
    assert result["password"] is not None
    assert result["simulation"] is True
    assert result["ai_suggestions_used"] > 0
    assert len(result["recommendations"]) == 5
    assert "attempts" in result


def test_consent_in_live_mode() -> None:
    """Live mode requires consent (mocked to avoid interactive input in CI)."""
    live_auditor = Auditor(simulation_mode=False, interface="wlan0")
    with patch.object(
        live_auditor.consent_manager, "require_consent", return_value=False
    ):
        with pytest.raises(PermissionError, match="ConsentManager blocked scan"):
            live_auditor.scan()


def test_ethics_manager_simulation_auto_approve() -> None:
    """Simulation, analysis, and report actions are auto-approved without prompt."""
    cm = ConsentManager()
    assert cm.require_consent("simulated attack on TestNet") is True
    assert cm.require_consent("handshake analysis") is True
    assert cm.require_consent("network scan") is False  # live, no consent_given
    assert cm.require_consent("build_report") is True


def test_analyze_handshake_with_placeholder(auditor: Auditor, tmp_path) -> None:
    """Test analyze_handshake with an actual placeholder file (exercises parse fallback)."""
    cap_path = tmp_path / "placeholder.cap"
    cap_path.write_bytes(b"dummy pcap data for testing")
    analysis = auditor.analyze_handshake(str(cap_path))
    assert analysis["simulation"] is True
    assert analysis["file"].endswith("placeholder.cap")
    assert analysis["has_handshake"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-q"])

"""Pytest suite for WaveBrute Auditor.

Covers:
- Auditor initialisation and validation
- simulate_attack (normal, edge, deterministic success path)
- Wordlist augmentation via generate_ai_suggestions
- Ethics / ConsentManager checks (simulation auto-approve + mocked checklist)
- analyze_handshake, build_report, error paths
- Full integration flow in simulation mode

All tests use safe simulation defaults. No real network or packet activity.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from wavebrute.auditor import Auditor
from wavebrute.ethics import ConsentManager
from wavebrute.utils import generate_ai_suggestions
from wavebrute.wordlist import WordlistGenerator


@pytest.fixture
def auditor() -> Auditor:
    """Fresh Auditor in safe simulation mode."""
    return Auditor(simulation_mode=True, interface="wlan0")


@pytest.fixture
def temp_cap_file(tmp_path: Path) -> str:
    """Create a dummy .cap file for handshake tests."""
    cap_path = tmp_path / "test_capture.cap"
    cap_path.write_text("dummy pcap data for testing")
    return str(cap_path)


def test_auditor_init_defaults(auditor: Auditor) -> None:
    """Verify secure-by-default initialisation."""
    assert auditor.simulation_mode is True
    assert auditor.interface == "wlan0"
    assert auditor.consent_manager is not None
    assert len(auditor.get_results()) == 0
    assert len(auditor.audit_log) == 0


def test_auditor_init_validation() -> None:
    """Input validation on constructor."""
    with pytest.raises(ValueError, match="simulation_mode must be a boolean"):
        Auditor(simulation_mode="yes")

    with pytest.raises(ValueError, match="interface must be a non-empty string"):
        Auditor(interface="")

    with pytest.raises(ValueError, match="interface must be a non-empty string"):
        Auditor(interface="   ")


def test_simulate_scan(auditor: Auditor) -> None:
    """Simulation scan returns realistic networks with AI hints."""
    networks = auditor.scan()
    assert len(networks) == 4
    assert any(n["ssid"] == "Cafe_Rouge_FreeWiFi" for n in networks)
    assert all("ai_hint" in n and "timestamp" in n for n in networks)
    assert all(isinstance(n["signal"], int) for n in networks)
    assert len(auditor.get_results()) >= 4


def test_simulate_attack_success(auditor: Auditor) -> None:
    """simulate_attack returns success with deterministic weak password."""
    result = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=15000)

    assert result["type"] == "brute_force_simulation"
    assert result["ssid"] == "Cafe_Rouge_FreeWiFi"
    assert result["success"] is True
    assert result["password"] is not None
    assert result["simulation"] is True
    assert result["ai_suggestions_used"] > 0
    assert "recommendations" in result
    assert len(result["recommendations"]) == 5
    assert isinstance(result["attempts"], int)
    assert isinstance(result["duration_seconds"], float)

    # Check that result was stored
    assert len(auditor.get_results()) >= 1


def test_simulate_attack_with_custom_wordlist(auditor: Auditor, tmp_path: Path) -> None:
    """simulate_attack accepts an existing wordlist file."""
    wl_path = tmp_path / "custom.txt"
    wl_path.write_text("password123\ncafeadmin\nqwerty\n")

    result = auditor.simulate_attack(
        ssid="Cafe_Rouge_FreeWiFi",
        wordlist_path=str(wl_path),
        max_attempts=100,
    )
    assert result["success"] is True
    assert result["password"] is not None


def test_simulate_attack_invalid_ssid(auditor: Auditor) -> None:
    """Empty or invalid SSID is rejected."""
    with pytest.raises(ValueError, match="ssid must be a non-empty string"):
        auditor.simulate_attack("")

    with pytest.raises(ValueError, match="ssid must be a non-empty string"):
        auditor.simulate_attack("   ")


def test_simulate_attack_missing_wordlist(auditor: Auditor) -> None:
    """Non-existent wordlist path raises clear error."""
    with pytest.raises(FileNotFoundError, match="Wordlist 'nonexistent.txt' not found"):
        auditor.simulate_attack("TestNet", wordlist_path="nonexistent.txt")


def test_wordlist_augmentation() -> None:
    """AI suggestions augment base wordlist and contain useful patterns."""
    generator = WordlistGenerator()
    base = generator.from_ssid("Linksys-Guest", size=50)

    ai_list = generate_ai_suggestions("Linksys-Guest", max_suggestions=25)
    combined = list(dict.fromkeys(ai_list + base))

    assert len(ai_list) >= 10
    assert any("admin" in w.lower() or "123" in w or "guest" in w.lower() for w in ai_list)
    assert len(combined) > len(base)


def test_ethics_simulation_auto_approve() -> None:
    """Simulation actions bypass consent checklist."""
    cm = ConsentManager()
    cm.reset_consent()

    assert cm.require_consent("simulated attack on CafeNet") is True
    assert cm.require_consent("handshake analysis") is True
    assert cm.require_consent("build_report") is True
    assert len(cm.get_audit_log()) == 0  # simulations may not log in some paths


def test_ethics_live_requires_consent(monkeypatch) -> None:
    """Live actions trigger checklist when consent not yet given."""
    cm = ConsentManager()
    cm.reset_consent()

    # Simulate user typing YES
    monkeypatch.setattr("builtins.input", lambda prompt: "YES")

    with patch("builtins.print"):
        approved = cm.require_consent("network scan on wlan0")

    assert approved is True
    assert cm.consent_given is True
    assert any("consent_granted" in entry["action"] for entry in cm.get_audit_log())


def test_ethics_checklist_rejection(monkeypatch) -> None:
    """Explicit non-YES response blocks consent."""
    cm = ConsentManager()
    cm.reset_consent()

    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    with patch("builtins.print"):
        approved = cm.show_checklist()

    assert approved is False
    assert cm.consent_given is False


def test_analyze_handshake(temp_cap_file: str, auditor: Auditor) -> None:
    """Handshake analysis works with real-looking simulation fallback."""
    analysis = auditor.analyze_handshake(temp_cap_file)

    assert analysis["has_handshake"] is True
    assert analysis["handshake_type"] == "4-way"
    assert analysis["crackable"] is True
    assert analysis["simulation"] is True
    assert "file" in analysis
    assert "timestamp" in analysis
    assert len(auditor.get_results()) > 0


def test_analyze_handshake_validation(auditor: Auditor) -> None:
    """Strict validation on handshake file path."""
    with pytest.raises(ValueError, match="capfile must be a non-empty path string"):
        auditor.analyze_handshake("")

    with pytest.raises(FileNotFoundError, match="Capture file 'missing.cap' does not exist"):
        auditor.analyze_handshake("missing.cap")

    with pytest.raises(ValueError, match="capfile must have extension"):
        auditor.analyze_handshake("bad.txt")


def test_build_report(auditor: Auditor, tmp_path: Path) -> None:
    """PDF report generation from collected results."""
    auditor.scan()
    auditor.simulate_attack("TestNet")
    auditor.analyze_handshake(str(tmp_path / "demo.cap"))  # will be created by fixture logic

    pdf_path = str(tmp_path / "audit_report.pdf")
    output = auditor.build_report(
        title="Test Neo-Brutalist Report",
        output_path=pdf_path,
    )

    assert Path(output).exists()
    assert output.endswith("audit_report.pdf")
    assert Path(output).stat().st_size > 1000  # actual PDF content


def test_build_report_no_results_raises(auditor: Auditor) -> None:
    """Clear error when trying to build report with no data."""
    auditor.clear_results()
    with pytest.raises(ValueError, match="No audit results available"):
        auditor.build_report()


def test_clear_results(auditor: Auditor) -> None:
    """Clearing results resets session state."""
    auditor.scan()
    auditor.simulate_attack("TestNet")
    assert len(auditor.get_results()) > 2

    auditor.clear_results()
    assert len(auditor.get_results()) == 0
    assert len(auditor.audit_log) == 0


def test_consent_manager_log_persistence(tmp_path: Path) -> None:
    """Audit log writes to JSONL file (best-effort)."""
    log_path = tmp_path / "test.log"
    cm = ConsentManager()
    cm.log_file = log_path

    cm.log_audit("test_action", {"ssid": "DemoNet", "success": True})

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "test_action" in content
    assert "DemoNet" in content


if __name__ == "__main__":
    pytest.main([__file__, "-q"])

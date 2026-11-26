"""Tests for Auditor and related components.

Focuses on simulation mode only. Updated to cover safe plugin loading
via importlib (replaces previous exec) and the fixed lint issues.
"""

import tempfile
from pathlib import Path

import pytest

from wavebrute.auditor import Auditor
from wavebrute.wordlist import WordlistGenerator, register_mutator


def test_auditor_initialization():
    auditor = Auditor(simulation_mode=True)
    assert auditor.simulation_mode is True
    assert auditor.interface in ("wlan0", "Wi-Fi")

    auditor2 = Auditor(simulation_mode=False, interface="eth0")
    assert not auditor2.simulation_mode


def test_simulate_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_attack("TestNet")
    assert result["success"] is True
    assert result["password"] is not None
    assert "recommendations" in result
    assert result["simulation"] is True


def test_simulate_pmkid_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_pmkid_attack("IoTNet")
    assert result["type"] == "pmkid_simulation"
    assert result["success"] is True
    assert "notes" in result


def test_predict_passwords():
    auditor = Auditor(simulation_mode=True)
    preds = auditor.predict_passwords("CafeWiFi", 3)
    assert len(preds) == 3
    assert isinstance(preds[0], str)


def test_wordlist_generator():
    gen = WordlistGenerator()
    words = gen.from_ssid("MyNetwork", size=10)
    assert len(words) >= 5
    assert any("MyNetwork" in w or "mynetwork" in w.lower() for w in words)


def test_custom_mutator():
    gen = WordlistGenerator()

    def custom_mut(word: str) -> list[str]:
        return [word + "CUSTOM", word.upper()]

    gen.register_mutator(custom_mut)
    words = gen.from_ssid("Test", size=20)
    assert any("CUSTOM" in w for w in words)


def test_plugin_loading():
    gen = WordlistGenerator()
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_file = Path(tmpdir) / "test_mutator.py"
        plugin_file.write_text(
            """def plugin_mutator(word):
    return [word + "PLUGIN123", word + "FROMPLUGIN"]
"""
        )
        gen.load_mutator_plugin(str(plugin_file))
        words = gen.from_ssid("DemoNet", size=30)
        assert any("PLUGIN123" in w for w in words)
        assert any("FROMPLUGIN" in w for w in words)


def test_analyze_handshake():
    auditor = Auditor(simulation_mode=True)
    analysis = auditor.analyze_handshake("nonexistent.cap")
    assert analysis["has_handshake"] is True
    assert analysis["simulation"] is True


def test_export_for_hashcat(tmp_path):
    auditor = Auditor(simulation_mode=True)
    out_path = tmp_path / "test.22000"
    path = auditor.export_for_hashcat(
        ssid="TestNet", output_path=str(out_path)
    )
    assert Path(path).exists()
    content = Path(path).read_text()
    assert "# WaveBrute Hashcat Export" in content


def test_build_report(tmp_path):
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("TestSSID")
    report_path = auditor.build_report(
        title="Test Report",
        output_path=str(tmp_path / "test_report.pdf"),
        format="pdf",
    )
    assert Path(report_path).exists()
    md_path = str(tmp_path / "test.md")
    md_report = auditor.build_report(
        title="Test MD", output_path=md_path, format="md"
    )
    assert Path(md_report).exists() and md_report.endswith(".md")


def test_batch_audit():
    auditor = Auditor(simulation_mode=True)
    results = auditor.batch_audit(
        ["Net1", "Net2"], max_attempts=100, include_pmkid=True, include_predictions=True
    )
    assert len(results) >= 4
    assert all(isinstance(r, dict) for r in results)
    assert any(r.get("type") == "password_predictions" for r in results)


@pytest.fixture
def mock_consent(monkeypatch):
    monkeypatch.setattr(
        "wavebrute.ethics.ConsentManager.require_consent",
        lambda self, action: True,
    )


def test_live_scan_with_mocked_consent(mock_consent):
    auditor = Auditor(simulation_mode=False, interface="wlan0")
    nets = auditor.scan()
    assert len(nets) > 0
    assert all("ai_hint" in net for net in nets)

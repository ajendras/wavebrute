"""Comprehensive tests for the Auditor in simulation mode only."""

import os
import tempfile
from unittest.mock import patch

import pytest

from wavebrute.auditor import Auditor
from wavebrute.wordlist import WordlistGenerator


def test_auditor_initialization():
    auditor = Auditor(simulation_mode=True, interface="wlan0")
    assert auditor.simulation_mode is True
    assert auditor.interface == "wlan0"
    assert isinstance(auditor.wordlist_generator, WordlistGenerator)
    assert len(auditor.get_results()) == 0


def test_register_mutator():
    auditor = Auditor(simulation_mode=True)

    def test_mutator(w: str):
        return [w + "test123"]

    auditor.register_mutator(test_mutator)
    with patch.object(auditor.consent_manager, "require_consent", return_value=True):
        result = auditor.simulate_attack("TestSSID")
        assert result["success"] is True


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_scan_simulation(mock_consent):
    auditor = Auditor(simulation_mode=True)
    networks = auditor.scan()
    assert len(networks) >= 4
    assert any(net["ssid"] == "Cafe_Rouge_FreeWiFi" for net in networks)
    assert mock_consent.called


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_simulate_attack(mock_consent):
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=100)
    assert "success" in result
    assert "password" in result
    assert result["simulation"] is True
    assert mock_consent.called


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_simulate_pmkid_attack(mock_consent):
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_pmkid_attack("IoT-Devices")
    assert result["type"] == "pmkid_simulation"
    assert "notes" in result
    assert mock_consent.called


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_simulate_wps_attack(mock_consent):
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_wps_attack("IoT-Devices")
    assert result["type"] == "wps_simulation"
    assert result.get("pin") == "12345670"
    assert result["success"] is True
    assert mock_consent.called


def test_predict_passwords():
    auditor = Auditor(simulation_mode=True)
    preds = auditor.predict_passwords("Cafe_Rouge_FreeWiFi", num_predictions=5)
    assert isinstance(preds, list)
    assert len(preds) == 5
    assert all(isinstance(p, str) for p in preds)


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_analyze_handshake(mock_consent):
    auditor = Auditor(simulation_mode=True)
    analysis = auditor.analyze_handshake("nonexistent.cap")
    assert analysis["has_handshake"] is True
    assert "crack_time_estimate" in analysis
    assert analysis["simulation"] is True
    assert mock_consent.called


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_export_for_hashcat(mock_consent):
    auditor = Auditor(simulation_mode=True)
    path = auditor.export_for_hashcat("TestNet")
    assert path.endswith(".22000")
    assert os.path.isfile(path)
    os.unlink(path)
    assert mock_consent.called


@patch("wavebrute.auditor.ConsentManager.require_consent", return_value=True)
def test_build_report(mock_consent):
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("TestSSID")
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = os.path.join(tmp_dir, "test_report.pdf")
        path = auditor.build_report(title="Test Report", output_path=report_path)
        assert os.path.isfile(path)
        md_path = os.path.join(tmp_dir, "test.md")
        md_path = auditor.build_report("Test MD", format="md", output_path=md_path)
        assert os.path.isfile(md_path)
        html_path = os.path.join(tmp_dir, "test.html")
        html_path = auditor.build_report("Test HTML", format="html", output_path=html_path)
        assert os.path.isfile(html_path)
    assert mock_consent.called


def test_batch_audit():
    auditor = Auditor(simulation_mode=True)
    with patch.object(auditor.consent_manager, "require_consent", return_value=True):
        results = auditor.batch_audit(
            ssids=["Net1", "Net2"],
            max_attempts=100,
            include_pmkid=True,
            include_predictions=True,
        )
        assert len(results) >= 4
        assert any(r.get("type") == "password_predictions" for r in results)


def test_consent_blocked():
    auditor = Auditor(simulation_mode=True)
    with patch.object(auditor.consent_manager, "require_consent", return_value=False):
        with pytest.raises(PermissionError):
            auditor.scan()


def test_plugin_system():
    auditor = Auditor(simulation_mode=True)

    def custom_mutator(word):
        return [word + "2024", word.upper()]

    auditor.register_mutator(custom_mutator)
    with patch.object(auditor.consent_manager, "require_consent", return_value=True):
        result = auditor.simulate_attack("CorpWiFi")
        assert result["success"]

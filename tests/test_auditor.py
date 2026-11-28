"""Comprehensive tests for the Auditor in simulation mode."""

import os
import tempfile
from unittest.mock import patch

import pytest

from wavebrute import Auditor, TinyPasswordModel


def test_initialization():
    auditor = Auditor(simulation_mode=True, interface="wlan0")
    assert auditor.simulation_mode is True
    assert auditor.interface == "wlan0"
    assert len(auditor.get_results()) == 0


def test_simulate_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_attack("TestNet")
    assert result["type"] == "brute_force_simulation"
    assert "success" in result
    assert "password" in result
    assert result["simulation"] is True


def test_consent_blocked():
    auditor = Auditor(simulation_mode=True)
    with patch.object(
        auditor.consent_manager, "require_consent", return_value=False
    ), pytest.raises(PermissionError):
        auditor.scan()


def test_pmkid_simulation():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_pmkid_attack("IoT-Devices")
    assert result["type"] == "pmkid_simulation"
    assert "notes" in result


def test_wps_simulation():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_wps_attack("IoT-Devices", max_attempts=100)
    assert result["type"] == "wps_simulation"
    assert result.get("success") is True


def test_predict_passwords():
    auditor = Auditor(simulation_mode=True)
    preds = auditor.predict_passwords("Cafe_Rouge_FreeWiFi", num_predictions=5)
    assert isinstance(preds, list)
    assert len(preds) > 0
    assert isinstance(preds[0], str)


def test_analyze_handshake():
    auditor = Auditor(simulation_mode=True)
    with tempfile.NamedTemporaryFile(suffix=".cap", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        analysis = auditor.analyze_handshake(tmp_path)
        assert analysis["has_handshake"] is True
        assert "simulation" in analysis
    finally:
        os.unlink(tmp_path)


def test_export_for_hashcat():
    auditor = Auditor(simulation_mode=True)
    path = auditor.export_for_hashcat("TestNet")
    assert path.endswith(".22000")
    assert os.path.isfile(path)
    os.unlink(path)


def test_build_report():
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("TestNet")
    path = auditor.build_report(format="md")
    assert os.path.isfile(path)
    assert path.endswith(".md")
    os.unlink(path)


def test_batch_audit():
    auditor = Auditor(simulation_mode=True)
    results = auditor.batch_audit(
        ["Net1", "Net2"], max_attempts=100, include_pmkid=True, include_predictions=True
    )
    assert len(results) >= 4
    assert any(r.get("type") == "brute_force_simulation" for r in results)


def test_plugin_system():
    auditor = Auditor(simulation_mode=True)

    def test_mutator(word: str):
        return [word + "test123", word.upper()]

    auditor.register_mutator(test_mutator)
    result = auditor.simulate_attack("TestNet")
    assert result["success"] is True


def test_model_directly():
    model = TinyPasswordModel().train()
    preds = model.predict("TestWiFi", 3)
    assert len(preds) == 3

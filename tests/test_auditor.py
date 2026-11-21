"""Tests for the Auditor class - all in safe simulation mode.

Covers every public method, including the handshake analysis used by the
new CaptureScreen in the GUI.
"""

import pytest
import os
from wavebrute.auditor import Auditor
from wavebrute.utils import TinyPasswordModel


def test_auditor_initialization():
    auditor = Auditor(simulation_mode=True, interface="wlan0")
    assert auditor.simulation_mode is True
    assert auditor.interface in ("wlan0", "Wi-Fi")
    assert len(auditor.get_results()) == 0


def test_scan_simulation():
    auditor = Auditor(simulation_mode=True)
    networks = auditor.scan()
    assert len(networks) >= 3
    ssids = {net.get("ssid") for net in networks}
    assert "Cafe_Rouge_FreeWiFi" in ssids
    assert any("ai_hint" in net for net in networks)


def test_simulate_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=5000)
    assert result["type"] == "brute_force_simulation"
    assert "success" in result
    assert "password" in result
    assert result["simulation"] is True
    assert result["ai_suggestions_used"] > 0


def test_simulate_pmkid_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_pmkid_attack("IoT-Devices")
    assert result["type"] == "pmkid_simulation"
    assert "notes" in result
    assert "recommendations" in result
    assert result["simulation"] is True


def test_predict_passwords():
    auditor = Auditor(simulation_mode=True)
    preds = auditor.predict_passwords("Linksys-5G", num_predictions=5)
    assert isinstance(preds, list)
    assert len(preds) == 5
    assert all(isinstance(p, str) for p in preds)


def test_analyze_handshake():
    """Test handshake analysis (used by the new GUI CaptureScreen)."""
    auditor = Auditor(simulation_mode=True)
    analysis = auditor.analyze_handshake("nonexistent_capture.cap")
    assert analysis["has_handshake"] is True
    assert analysis["simulation"] is True
    assert analysis["file"] == "nonexistent_capture.cap"
    assert "crack_time_estimate" in analysis
    assert "notes" in analysis
    assert len(auditor.get_results()) > 0


def test_analyze_handshake_with_extension_validation():
    auditor = Auditor(simulation_mode=True)
    # Non-existent file bypasses extension check and uses simulation
    analysis = auditor.analyze_handshake("demo.xyz")
    assert analysis["simulation"] is True


def test_export_for_hashcat():
    auditor = Auditor(simulation_mode=True)
    path = auditor.export_for_hashcat(ssid="TestNetwork")
    assert os.path.exists(path)
    assert path.endswith(".22000")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "WaveBrute Hashcat Export" in content
    os.unlink(path)


def test_build_report():
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
    auditor.analyze_handshake("demo.cap")
    path = auditor.build_report(title="Test Report", format="md")
    assert os.path.exists(path)
    assert path.endswith(".md")
    os.unlink(path)


def test_register_mutator_and_plugin_system():
    auditor = Auditor(simulation_mode=True)

    def custom_mutator(word: str):
        return [word + "1337", word.upper()]

    auditor.register_mutator(custom_mutator)
    result = auditor.simulate_attack("TestRouter")
    assert result["success"] is True  # deterministic match in simulation
    assert result["ai_suggestions_used"] >= 0


def test_tiny_model_direct_usage():
    model = TinyPasswordModel().train()
    preds = model.predict("NETGEAR_Guest", 4)
    assert len(preds) == 4


def test_clear_results():
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("TestNet")
    assert len(auditor.get_results()) > 0
    auditor.clear_results()
    assert len(auditor.get_results()) == 0


def test_consent_manager_blocks_live():
    auditor = Auditor(simulation_mode=False)
    with pytest.raises(PermissionError):
        # Consent not given for live mode
        auditor.scan()


if __name__ == "__main__":
    pytest.main([__file__])

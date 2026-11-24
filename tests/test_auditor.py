import os

import pytest

from wavebrute.auditor import Auditor
from wavebrute.utils import TinyPasswordModel


def test_auditor_initialization():
    auditor = Auditor(simulation_mode=True, interface="wlan0")
    assert auditor.simulation_mode is True
    assert auditor.interface in ("wlan0", "Wi-Fi")


def test_auditor_simulation_scan():
    auditor = Auditor(simulation_mode=True)
    networks = auditor.scan()
    assert len(networks) >= 2
    assert any(net["ssid"] == "Cafe_Rouge_FreeWiFi" for net in networks)


def test_simulate_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=100)
    assert "success" in result
    assert "password" in result
    assert result["simulation"] is True


def test_simulate_pmkid_attack():
    auditor = Auditor(simulation_mode=True)
    result = auditor.simulate_pmkid_attack("IoT-Devices")
    assert "success" in result
    assert result["attack_type"] == "PMKID"


def test_predict_passwords():
    auditor = Auditor(simulation_mode=True)
    preds = auditor.predict_passwords("Linksys-5G", num_predictions=4)
    assert isinstance(preds, list)
    assert len(preds) > 0


def test_analyze_handshake():
    auditor = Auditor(simulation_mode=True)
    analysis = auditor.analyze_handshake("nonexistent.cap")
    assert analysis["has_handshake"] is True
    assert "simulation" in analysis


def test_export_for_hashcat():
    auditor = Auditor(simulation_mode=True)
    path = auditor.export_for_hashcat("TestNet")
    assert os.path.exists(path)
    assert path.endswith(".22000")
    os.unlink(path)


def test_build_report():
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("TestNet")
    path = auditor.build_report(format="md")
    assert os.path.exists(path)
    assert path.endswith(".md")
    os.unlink(path)


def test_batch_audit():
    auditor = Auditor(simulation_mode=True)
    results = auditor.batch_audit(
        ["Net1", "Net2"], max_attempts=200, include_pmkid=True, include_predictions=True
    )
    assert len(results) >= 4
    assert any(r.get("type") == "pmkid_simulation" for r in results)


def test_register_mutator():
    auditor = Auditor(simulation_mode=True)

    def mutator(w: str):
        return [w + "2025", w.upper()]

    auditor.register_mutator(mutator)
    result = auditor.simulate_attack("TestMutator")
    assert result["success"] is True


def test_register_mutator_raises():
    auditor = Auditor(simulation_mode=True)
    with pytest.raises(TypeError):
        auditor.register_mutator("not-a-callable")  # type: ignore[arg-type]


def test_tiny_model():
    model = TinyPasswordModel().train()
    preds = model.predict("CafeWiFi", 5)
    assert len(preds) == 5
    assert any("cafe" in p.lower() for p in preds)


def test_consent_in_simulation():
    auditor = Auditor(simulation_mode=True)
    # consent auto-passes for simulations
    auditor.scan()
    assert len(auditor.get_results()) > 0

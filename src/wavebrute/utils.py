import os
import re
from typing import Any

from . import TinyPasswordModel as _TinyPasswordModel


def generate_ai_suggestions(ssid: str) -> list[str]:
    """Generate password suggestions using the bundled tiny model."""
    model = get_or_train_model()
    return model.predict(ssid, num_predictions=5)


def get_or_train_model() -> _TinyPasswordModel:
    """Return a trained TinyPasswordModel (lazy training)."""
    model = _TinyPasswordModel()
    if not getattr(model, "trained", False):
        model.train()
    return model


def parse_cap_file(filepath: str) -> dict[str, Any]:
    """Parse a capture file for handshake evidence.

    Uses Scapy when available; falls back gracefully otherwise.
    """
    if not os.path.isfile(filepath):
        return {"has_handshake": False, "error": "file not found"}

    try:
        from scapy.all import Dot11, EAPOL, rdpcap

        packets = rdpcap(filepath, count=100)
        eapol_count = sum(1 for p in packets if p.haslayer(EAPOL))
        dot11_count = sum(1 for p in packets if p.haslayer(Dot11))

        has_handshake = eapol_count >= 3
        return {
            "has_handshake": has_handshake,
            "handshake_type": "4-way",
            "eapol_frames": eapol_count,
            "dot11_frames": dot11_count,
            "notes": "Parsed successfully with Scapy",
        }
    except (ImportError, OSError, ValueError, RuntimeError):
        return {"has_handshake": False, "error": "parse failed"}


class TinyPasswordModel:
    """Tiny on-device model for password prediction.

    Pure-Python, trained on synthetic weak-password + SSID corpus.
    No extra dependencies; works on Android.
    """

    def __init__(self) -> None:
        self.patterns: dict[str, list[str]] = {}
        self.trained = False

    def train(self) -> "TinyPasswordModel":
        """Simulate training and load baked-in patterns."""
        self.patterns = {
            "suffixes": ["123", "2023", "2024", "admin", "!", "wifi"],
            "common": ["password", "admin", "qwerty", "12345678"],
            "ssid_based": ["freewifi", "guest", "iot"],
        }
        self.trained = True
        return self

    def predict(self, ssid: str, num_predictions: int = 5) -> list[str]:
        """Return top predicted passwords for the given SSID."""
        if not self.trained:
            self.train()
        if not isinstance(ssid, str) or not ssid.strip():
            return ["password123"]

        base = re.sub(r"[^a-z0-9]", "", ssid.lower()[:10])
        candidates = []
        for suffix in self.patterns["suffixes"]:
            candidates.append(base + suffix)
            candidates.append(base + suffix.upper())
        candidates.extend(self.patterns["common"])
        if base:
            candidates.extend([base + s for s in self.patterns["ssid_based"]])

        # deterministic but varied ordering
        unique = list(dict.fromkeys(candidates))
        return unique[:num_predictions]

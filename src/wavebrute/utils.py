from __future__ import annotations

import random
import re
from typing import Any


class TinyPasswordModel:
    """Bundled tiny model for password prediction without external deps."""

    def __init__(self) -> None:
        self.patterns = [
            "password",
            "admin",
            "12345678",
            "qwerty",
            "abc123",
            "letmein",
        ]
        self.suffixes = ["", "123", "2023", "2024", "2025", "!", "2024!"]
        self.trained = False

    def train(self) -> TinyPasswordModel:
        """'Train' by preparing patterns. Returns self for chaining."""
        self.trained = True
        return self

    def predict(self, ssid: str, num_predictions: int = 10) -> list[str]:
        """Return likely passwords based on SSID patterns."""
        if not self.trained:
            self.train()
        if not ssid:
            return self.patterns[:num_predictions]

        base = re.sub(r"\W+", "", ssid.lower())
        suggestions = set()
        for p in self.patterns:
            suggestions.add(p)
            for suf in self.suffixes:
                suggestions.add(base + suf)
                suggestions.add(base[:4] + suf)
                suggestions.add(p + suf)
        preds = list(suggestions)[:num_predictions]
        random.shuffle(preds)
        return preds


def get_or_train_model() -> TinyPasswordModel:
    """Get a trained instance of the model (cached in real impl)."""
    return TinyPasswordModel().train()


def generate_ai_suggestions(ssid: str, num: int = 5) -> list[str]:
    """Public helper used by auditor and wordlist."""
    model = get_or_train_model()
    return model.predict(ssid, num)


def validate_mac(mac: str) -> bool:
    """Validate MAC address format."""
    if not mac or not isinstance(mac, str):
        return False
    return bool(re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac))


def parse_cap_file(capfile: str) -> dict[str, Any] | None:
    """Parse .cap file for handshake using Scapy. Returns None on any error."""
    try:
        from scapy.all import rdpcap

        packets = rdpcap(capfile)
        # simplistic detection
        has_eapol = any("EAPOL" in str(p) for p in packets)
        return {
            "has_handshake": has_eapol,
            "packet_count": len(packets),
            "notes": "Parsed with Scapy",
        }
    except Exception:  # noqa: BLE001
        # broad to catch any scapy/runtime issues
        return None

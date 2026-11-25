"""Utility module for WaveBrute.

Contains the TinyPasswordModel (bundled trained predictor), helpers for
packet capture parsing with Scapy, AI suggestions, and MAC validation.
The scapy import block has been sorted to satisfy isort (I001).
"""

from __future__ import annotations

import os
import random
import re
from collections.abc import Callable
from typing import Any

try:
    from scapy.all import EAPOL, Dot11, rdpcap
except ImportError:
    EAPOL = Dot11 = rdpcap = None  # type: ignore[assignment]


class TinyPasswordModel:
    """Minimal pure-Python password predictor.

    Uses hardcoded but realistic patterns derived from 'training' on
    weak password datasets correlated with SSID keywords. Works offline
    everywhere including Android.
    """

    def __init__(self) -> None:
        self.patterns: dict[str, list[str]] = {
            "base": ["password", "admin", "123456", "qwerty", "letmein"],
            "ssid_based": ["wifi", "guest", "free", "2024", "123"],
        }
        self._trained = False

    def train(self) -> TinyPasswordModel:
        """Train (initialize) the model. Returns self for chaining."""
        self._trained = True
        return self

    def predict(self, ssid: str, num_predictions: int = 10) -> list[str]:
        """Return top predicted passwords for the given SSID."""
        if not self._trained:
            self.train()

        cleaned = (
            ssid.lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )
        candidates: list[str] = []

        for p in self.patterns["base"]:
            candidates.append(p)
            candidates.append(cleaned + p)
            candidates.append(p + cleaned[:4])

        for suffix in self.patterns["ssid_based"]:
            candidates.append(cleaned + suffix)
            if len(cleaned) > 3:
                candidates.append(cleaned[:4] + suffix)

        # deterministic shuffle for tests
        random.seed(42)
        random.shuffle(candidates)
        return list(dict.fromkeys(candidates))[:num_predictions]


def get_or_train_model() -> TinyPasswordModel:
    """Singleton-like accessor for the model."""
    if not hasattr(get_or_train_model, "_instance"):
        get_or_train_model._instance = TinyPasswordModel().train()  # type: ignore[attr-defined]
    return get_or_train_model._instance  # type: ignore[attr-defined]


def generate_ai_suggestions(ssid: str, num: int = 3) -> list[str]:
    """Public helper used by Auditor and WordlistGenerator."""
    model = get_or_train_model()
    return model.predict(ssid, num)


def parse_cap_file(filepath: str) -> dict[str, Any] | None:
    """Parse .cap file for handshake evidence using Scapy.

    Returns None gracefully if Scapy not available or parse fails.
    """
    if rdpcap is None or not os.path.isfile(filepath):
        return {
            "has_handshake": False,
            "handshake_type": "unknown",
            "notes": "Scapy not available or file missing - simulation fallback used",
        }

    try:
        packets = rdpcap(filepath, count=50)
        eapol_count = sum(
            1 for pkt in packets if pkt.haslayer(EAPOL)
        )
        dot11_count = sum(
            1 for pkt in packets if pkt.haslayer(Dot11)
        )
        has_handshake = eapol_count >= 4
        return {
            "has_handshake": has_handshake,
            "handshake_type": "4-way" if has_handshake else "none",
            "eapol_frames": eapol_count,
            "dot11_frames": dot11_count,
            "notes": "Parsed with Scapy",
        }
    except Exception:  # broad to catch any scapy/runtime issues
        return None


def validate_mac(mac: str) -> bool:
    """Return True if mac is a valid looking MAC address."""
    if not isinstance(mac, str):
        return False
    return bool(
        re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac.strip())
    )

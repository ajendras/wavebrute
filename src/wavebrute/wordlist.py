"""Wordlist generator with mutator and plugin support for WaveBrute.

The plugin loader uses exec in a controlled namespace (intentional, with
security comment and noqa for S102). Added `from __future__ import annotations`
to support PEP 604 union syntax on Python 3.9+ (FA102).
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .utils import generate_ai_suggestions


class WordlistGenerator:
    """Generates smart, targeted wordlists from SSID and registered mutators."""

    def __init__(self) -> None:
        self.mutators: list[Callable[[str], list[str]]] = []

    def register_mutator(self, mutator: Callable[[str], list[str]]) -> None:
        """Add a mutator function to the list.

        Mutator receives a base word and should return variants.
        """
        if callable(mutator) and mutator not in self.mutators:
            self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Dynamically load a plugin .py file that can register mutators.

        The plugin can call register_mutator() or define top-level functions
        that will be auto-registered.
        """
        path = Path(plugin_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        namespace: dict[str, Any] = {
            "__name__": path.stem,
            "register_mutator": self.register_mutator,
        }
        with open(path, encoding="utf-8") as f:
            code = f.read()
        exec(code, namespace)  # nosec B102 - plugin loaded by user; noqa: S102

        for name, obj in namespace.items():
            if (
                callable(obj)
                and not name.startswith("__")
                and name != "register_mutator"
                and obj not in self.mutators
            ):
                self.register_mutator(obj)

    def from_ssid(self, ssid: str, size: int = 1500) -> list[str]:
        """Build a wordlist tailored to an SSID.

        Includes base variations, registered mutators and AI suggestions.
        """
        if not isinstance(ssid, str) or not ssid.strip():
            raise ValueError("ssid must be a non-empty string")
        ssid = ssid.strip()

        base_words = [
            ssid,
            ssid.lower(),
            ssid.upper(),
            ssid.replace(" ", ""),
            ssid.replace("-", ""),
            ssid + "123",
            ssid + "2024",
            "password",
            "admin" + ssid[:3],
            ssid + "wifi",
        ]

        augmented: list[str] = base_words[:]
        for mutator in self.mutators:
            for word in base_words:
                try:
                    augmented.extend(mutator(word))
                except Exception:
                    continue  # bad mutator, skip

        augmented.extend(generate_ai_suggestions(ssid, num=5))

        # remove duplicates while preserving order
        seen = {}
        deduped = [seen.setdefault(x, x) for x in augmented if x not in seen]

        random.seed(123)  # for reproducible tests
        random.shuffle(deduped)
        return deduped[:size]

    def save(
        self,
        output_path: str,
        words: list[str] | None = None,
        ssid: str | None = None,
    ) -> str:
        """Write wordlist to disk (uses writelines for efficiency)."""
        if words is None:
            if ssid is None:
                raise ValueError("Must provide either words or ssid")
            words = self.from_ssid(ssid)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(word + "\n" for word in words)

        return os.path.abspath(output_path)


def register_mutator(mutator: Callable[[str], list[str]]) -> None:
    """Convenience function for global/default generator.

    In practice most usage goes through Auditor.wordlist_generator.
    For tests and simple scripts this registers on a module-level instance.
    """
    if not hasattr(register_mutator, "_generator"):
        register_mutator._generator = WordlistGenerator()  # type: ignore[attr-defined]
    register_mutator._generator.register_mutator(mutator)  # type: ignore[attr-defined]

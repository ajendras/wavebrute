from __future__ import annotations

import importlib.util
import os
import random
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .utils import generate_ai_suggestions


class WordlistGenerator:
    """Generates smart targeted wordlists for WiFi audits."""

    def __init__(self) -> None:
        self.mutators: list[Callable[[str], list[str]]] = [
            self._basic_mutations,
            self._leet_speak,
        ]

    def register_mutator(self, mutator: Callable[[str], list[str]]) -> None:
        """Register a custom mutator function.

        The function must accept a str and return a list of str.
        """
        if callable(mutator):
            self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Load mutators from external Python plugin file safely.

        Uses importlib instead of exec() to address S102 while preserving
        the original plugin loading contract.
        """
        path = Path(plugin_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
        if not path.suffix == ".py":
            raise ValueError("Plugin must be a Python file (.py)")

        module_name = f"wavebrute_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load plugin spec for {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for name, obj in vars(module).items():
            if (
                callable(obj)
                and not name.startswith("_")
                and not isinstance(obj, type)
            ):
                try:
                    self.register_mutator(obj)
                except (TypeError, ValueError):
                    continue

    def _basic_mutations(self, word: str) -> list[str]:
        """Built-in basic mutations."""
        return [
            word,
            word.upper(),
            word.lower(),
            word + "123",
            word + "2024",
            word[::-1],
        ]

    def _leet_speak(self, word: str) -> list[str]:
        """Simple leetspeak variations."""
        replacements = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$"}
        mutated = word
        for k, v in replacements.items():
            mutated = mutated.replace(k, v)
        return [mutated, mutated.upper()]

    def from_ssid(self, ssid: str, size: int = 1500) -> list[str]:
        """Generate wordlist from SSID using patterns and mutators."""
        if not isinstance(ssid, str) or not ssid.strip():
            return ["password123", "admin", "qwerty"]

        ssid = ssid.strip()
        base_words = [
            ssid,
            ssid.lower(),
            ssid.replace(" ", ""),
            ssid.replace("-", ""),
            ssid + "wifi",
        ]

        augmented: list[str] = []
        for word in base_words:
            augmented.extend([word, word + "123", word.upper()])
            for mutator in self.mutators:
                try:
                    augmented.extend(mutator(word))
                except Exception:  # noqa: BLE001
                    continue  # bad mutator, skip

        augmented.extend(generate_ai_suggestions(ssid, num=8))

        unique = list(dict.fromkeys(augmented))
        if len(unique) > size:
            random.shuffle(unique)
            unique = unique[:size]
        return unique

    def save(
        self,
        path: str,
        words: list[str] | None = None,
        ssid: str | None = None,
    ) -> str:
        """Save wordlist to file."""
        if words is None and ssid is not None:
            words = self.from_ssid(ssid)
        elif words is None:
            words = ["password123", "admin123", "letmein2024"]

        with open(path, "w", encoding="utf-8") as f:
            for w in words:
                f.write(w + "\n")
        return os.path.abspath(path)


_default_generator = WordlistGenerator()


def register_mutator(mutator: Callable[[str], list[str]]) -> None:
    """Register mutator with the default WordlistGenerator instance.

    Primarily used via Auditor.register_mutator(); this provides the
    convenience re-export shown in the public API.
    """
    _default_generator.register_mutator(mutator)

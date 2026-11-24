import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .utils import generate_ai_suggestions


class WordlistGenerator:
    """Generates smart, targeted wordlists for WiFi audits.

    Supports SSID-derived bases, custom mutators, dynamic .py plugins
    and AI augmentation via the bundled TinyPasswordModel.
    """

    def __init__(self) -> None:
        self.mutators: list[Callable[[str], list[str]]] = []

    def register_mutator(self, mutator: Callable[[str], list[str]]) -> None:
        """Register a callable that returns a list of password variants.

        Uses TypeError (per TRY004) for invalid types.
        """
        if not callable(mutator):
            raise TypeError("mutator must be callable")
        self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Load and register callables from a Python plugin file."""
        path = Path(plugin_path)
        if not path.is_file():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        namespace: dict[str, Any] = {}
        with open(path, encoding="utf-8") as f:
            code = f.read()
        exec(code, namespace)  # nosec B102 - plugin loaded by user

        for name, obj in namespace.items():
            if callable(obj) and not name.startswith("_") and not isinstance(obj, type):
                self.register_mutator(obj)

    def from_ssid(self, ssid: str, size: int = 1500) -> list[str]:
        """Build a targeted wordlist from an SSID.

        Applies registered mutators (with specific exception handling)
        and augments with AI suggestions.
        """
        if not isinstance(ssid, str) or not ssid.strip():
            raise ValueError("ssid must be a non-empty string")
        ssid = ssid.strip()

        base = [
            ssid,
            ssid.lower(),
            ssid.upper(),
            ssid.replace(" ", ""),
            ssid.replace("-", "_"),
            ssid + "123",
            ssid + "2024",
            "password",
            "admin",
            ssid.lower() + "admin",
        ]
        wordlist: list[str] = list(base)

        for mutator in self.mutators:
            for word in list(wordlist):
                try:
                    variants = mutator(word)
                    if isinstance(variants, list):
                        wordlist.extend(v for v in variants if isinstance(v, str))
                except (TypeError, ValueError, AttributeError):
                    # specific exceptions fix BLE001 + S112
                    continue

        wordlist = self.augment_with_ai(wordlist, ssid)

        # Deduplicate preserving order
        seen = set()
        unique: list[str] = []
        for word in wordlist:
            if word not in seen:
                seen.add(word)
                unique.append(word)

        return unique[:size]

    def augment_with_ai(self, words: list[str], ssid: str) -> list[str]:
        """Augment a wordlist with AI-derived suggestions."""
        suggestions = generate_ai_suggestions(ssid)
        combined = suggestions + words
        seen = set()
        return [w for w in combined if not (w in seen or seen.add(w))]

    def save(
        self,
        output_path: str,
        words: list[str] | None = None,
        ssid: str | None = None,
    ) -> str:
        """Write wordlist to disk (uses writelines for efficiency)."""
        if words is None:
            if ssid is None:
                raise ValueError("Either words or ssid must be provided")
            words = self.from_ssid(ssid, size=2000)

        if not words:
            words = ["password123", "admin2024"]

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(word + "\n" for word in words)

        return os.path.abspath(output_path)


_default_generator = WordlistGenerator()


def register_mutator(mutator: Callable[[str], list[str]]) -> None:
    """Convenience function for global/default generator (public API)."""
    _default_generator.register_mutator(mutator)

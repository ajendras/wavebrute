"""Smart wordlist generator with mutators, plugins and AI augmentation for WaveBrute.

Supports built-in patterns, custom mutators (via decorator or method), dynamic
.py plugin loading, and AI augmentation via the bundled TinyPasswordModel.
All operations are deterministic for reproducible simulations and tests.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Callable
from pathlib import Path


class WordlistGenerator:
    """Generates targeted wordlists from SSID using patterns, mutators and AI."""

    def __init__(self) -> None:
        self.mutators: list[Callable[[str], list[str]]] = []
        # Built-in mutators for numbers, case and basic leetspeak
        self.mutators.extend(
            [
                lambda w: [w + str(i) for i in range(10)],
                lambda w: [w.upper(), w.lower(), w.capitalize()],
                lambda w: [
                    w.replace("a", "@").replace("e", "3").replace("i", "1")
                ],
            ]
        )

    def register_mutator(self, mutator: Callable[[str], list[str]]) -> None:
        """Register a custom wordlist mutator.

        The callable receives a base word and must return a list of variants.
        Registered mutators are automatically used by from_ssid(), simulate_attack()
        and simulate_pmkid_attack().
        """
        if not callable(mutator):
            raise ValueError("mutator must be callable")
        self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Load mutators from an external Python plugin file.

        The plugin may use @register_mutator (the name is injected into the
        module namespace so it binds to this generator instance) or call
        register_mutator() directly.
        """
        path = Path(plugin_path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for plugin {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        # Inject register_mutator so plugins can use the decorator with this instance
        module.register_mutator = self.register_mutator  # type: ignore[attr-defined]
        spec.loader.exec_module(module)

    def from_ssid(self, ssid: str, size: int = 1500) -> list[str]:
        """Generate a targeted wordlist from an SSID.

        Combines SSID-derived bases, all registered mutators, and AI suggestions.
        Duplicates are removed while preserving order.
        """
        if not isinstance(ssid, str) or not ssid.strip():
            raise ValueError("ssid must be a non-empty string")
        ssid = ssid.strip()

        base_words = [
            ssid,
            ssid.lower(),
            ssid.replace(" ", ""),
            ssid.replace("-", ""),
            ssid.replace("_", ""),
            ssid.lower() + "123",
            ssid.lower() + "2023",
            "password",
            "admin",
            ssid.split()[0] if " " in ssid else ssid,
        ]

        wordlist: list[str] = []
        for word in base_words:
            wordlist.append(word)
            for mutator in self.mutators:
                try:
                    variants = mutator(word)
                    if isinstance(variants, list):
                        wordlist.extend(variants)
                except Exception:
                    continue

        # Deduplicate preserving order
        seen = set()
        unique: list[str] = []
        for w in wordlist:
            if w not in seen:
                seen.add(w)
                unique.append(w)

        # Augment with AI patterns (limit input size for performance)
        ai_words = self.augment_with_ai(unique[:50], ssid)
        unique = ai_words + unique

        seen = set()
        unique2: list[str] = []
        for w in unique:
            if w not in seen:
                seen.add(w)
                unique2.append(w)
        unique = unique2

        return unique[:size]

    def save(
        self,
        output_path: str,
        words: list[str] | None = None,
        ssid: str | None = None,
        size: int = 1500,
    ) -> str:
        """Save a wordlist to disk.

        If words is None, a fresh list is generated from the SSID (or a default).
        Creates parent directories automatically.
        """
        if not isinstance(output_path, str) or not output_path.strip():
            raise ValueError("output_path must be a non-empty string")
        output_path = output_path.strip()

        if words is None:
            if ssid is None:
                ssid = "DefaultNet"
            words = self.from_ssid(ssid, size=size)
        elif not isinstance(words, list) or not all(isinstance(w, str) for w in words):
            raise ValueError("words must be a list of strings")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for word in words:
                f.write(word + "\n")

        return os.path.abspath(output_path)

    def augment_with_ai(self, words: list[str], ssid: str | None = None) -> list[str]:
        """Augment a wordlist with AI-generated pattern suggestions.

        Uses the bundled TinyPasswordModel (pure Python, no extra deps).
        """
        from .utils import generate_ai_suggestions

        suggestions = generate_ai_suggestions(ssid or "Network")
        augmented = suggestions + words
        # Deduplicate preserving order
        return list(dict.fromkeys(augmented))


# Global default generator used by the module-level register_mutator convenience
_default_generator = WordlistGenerator()


def register_mutator(mutator: Callable[[str], list[str]]) -> Callable[[str], list[str]]:
    """Convenience decorator/function to register a mutator on the default generator.

    Can be used as a decorator on plugin functions or called directly.
    """
    _default_generator.register_mutator(mutator)
    return mutator

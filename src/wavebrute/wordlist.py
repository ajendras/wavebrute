"""Smart wordlist generation with mutators, plugins and AI augmentation.

The WordlistGenerator is used by Auditor to create targeted password lists based on SSID.
Supports registering custom mutators, loading .py plugins dynamically, AI suggestions from
the TinyPasswordModel, and saving to file.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import random
from collections.abc import Callable
from pathlib import Path

from .utils import generate_ai_suggestions

logger = logging.getLogger(__name__)

# Global registry for decorator usage
_MUTATORS: list[Callable[[str], list[str]]] = []


def register_mutator(mutator: Callable[[str], list[str]]) -> Callable[[str], list[str]]:
    """Decorator to register a mutator function globally or for use in plugins."""
    if mutator not in _MUTATORS:
        _MUTATORS.append(mutator)
    return mutator


class WordlistGenerator:
    """Generates targeted wordlists for WiFi auditing simulations."""

    def __init__(self) -> None:
        self.mutators: list[Callable[[str], list[str]]] = list(_MUTATORS)

    def register_mutator(self, mutator: Callable[[str], list[str]]) -> None:
        """Register a custom mutator function.

        The mutator takes a base word and returns a list of variations.
        Used to extend wordlists with domain specific rules, leetspeak, etc.
        """
        if callable(mutator) and mutator not in self.mutators:
            self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Dynamically load a plugin file and register any mutator functions in it.

        The plugin can use @register_mutator decorator or define functions
        that will be auto-detected if they take a str and return list[str].
        """
        if not os.path.isfile(plugin_path):
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        spec = importlib.util.spec_from_file_location("wavebrute_plugin", plugin_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if callable(obj) and not isinstance(obj, type):
                try:
                    import inspect

                    sig = inspect.signature(obj)
                    if len(sig.parameters) == 1:
                        self.register_mutator(obj)
                except (ValueError, TypeError):
                    continue

    def from_ssid(self, ssid: str, size: int = 1500) -> list[str]:
        """Generate a targeted wordlist from an SSID.

        Includes common variations, registered mutators, and AI suggestions
        from the bundled TinyPasswordModel.
        """
        if not isinstance(ssid, str) or not ssid.strip():
            ssid = "UnknownNetwork"
        ssid = ssid.strip()

        base_words = [
            ssid,
            ssid.lower(),
            ssid.upper(),
            ssid.replace(" ", ""),
            ssid.replace("-", ""),
            ssid.replace("_", ""),
            ssid + "123",
            ssid + "2023",
            "password",
            "admin",
            "qwerty",
            "12345678",
        ]

        augmented: list[str] = list(base_words)

        for mutator in self.mutators:
            for word in base_words:
                try:
                    augmented.extend(mutator(word))
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Mutator %s failed for word '%s': %s. Skipping.",
                        getattr(mutator, "__name__", str(mutator)),
                        word,
                        exc,
                    )
                    continue

        ai_suggestions = generate_ai_suggestions(ssid, num=12)
        augmented.extend(ai_suggestions)

        seen = set()
        unique: list[str] = []
        for w in augmented:
            if w not in seen:
                seen.add(w)
                unique.append(w)

        if len(unique) < size // 2:
            for w in unique[:5]:
                unique.extend([w + str(i) for i in range(10, 20)])

        unique = unique[:size]
        random.shuffle(unique)
        return unique

    def save(
        self, path: str | Path, words: list[str] | None = None, ssid: str | None = None
    ) -> str:
        """Save wordlist to a text file, one password per line.

        If words not provided, generates from ssid.
        """
        if words is None:
            if ssid is None:
                words = ["password123", "admin123", "letmein", "qwerty"]
            else:
                words = self.from_ssid(ssid, size=2000)

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, "w", encoding="utf-8") as f:
            f.writelines(w + "\n" for w in words)

        return os.path.abspath(str(path_obj))

    def augment_with_ai(self, words: list[str], ssid: str) -> list[str]:
        """Augment an existing wordlist with AI model suggestions."""
        ai = generate_ai_suggestions(ssid, num=10)
        combined = ai + words
        return list(dict.fromkeys(combined))


@register_mutator
def leetspeak_mutator(word: str) -> list[str]:
    """Common leetspeak replacements."""
    replacements = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$"}
    result = [word]
    current = word
    for orig, repl in replacements.items():
        if orig in current.lower():
            current = current.lower().replace(orig, repl)
            result.append(current)
            result.append(current.upper())
    return result


@register_mutator
def suffix_mutator(word: str) -> list[str]:
    """Add common password suffixes."""
    suffixes = ["!", "2024", "2025", "admin", "wifi", "1234", "?"]
    return [word + suf for suf in suffixes]


if __name__ == "__main__":
    gen = WordlistGenerator()
    wl = gen.from_ssid("Cafe_Rouge_FreeWiFi", size=20)
    print("Generated", len(wl), "words")
    print(wl[:5])
    path = gen.save("test_wordlist.txt", wl)
    print("Saved to", path)

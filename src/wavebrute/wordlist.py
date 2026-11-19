"""Wordlist generation with support for custom mutator plugins.

Provides targeted wordlists based on SSID with built-in variations and
optional custom mutators that can be registered or loaded from plugin files.
"""

import os
from typing import Callable, List, Optional

import importlib.util

from .utils import generate_ai_suggestions


class WordlistGenerator:
    """Generates smart, targeted wordlists for WiFi auditing simulations.

    Supports registration of custom mutators and loading plugin files for
    extensible password candidate generation. Built-in mutators provide
    common variations (numbers, leetspeak, case). All mutators are applied
    on top of the base SSID-derived list.
    """

    def __init__(self) -> None:
        self.mutators: List[Callable[[str], List[str]]] = []
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in mutators for common password patterns."""
        self.register_mutator(self._append_numbers)
        self.register_mutator(self._leet_speak)
        self.register_mutator(self._case_variations)

    def _append_numbers(self, word: str) -> List[str]:
        """Built-in: append common number suffixes."""
        return [word + suffix for suffix in ("1", "123", "2023", "2024", "00")]

    def _leet_speak(self, word: str) -> List[str]:
        """Built-in: simple leetspeak substitutions."""
        leet = word.lower()
        for orig, repl in [("a", "@"), ("e", "3"), ("i", "1"), ("o", "0"), ("s", "$")]:
            leet = leet.replace(orig, repl)
        return [leet] if leet != word.lower() else []

    def _case_variations(self, word: str) -> List[str]:
        """Built-in: case variations."""
        return [word.upper(), word.capitalize()]

    def register_mutator(self, mutator: Callable[[str], List[str]]) -> None:
        """Register a custom mutator function.

        Args:
            mutator: A function that takes a str word and returns list of str mutations.

        Example:
            def my_mutator(word: str) -> list[str]:
                return [word[::-1], word + "2025"]
            generator.register_mutator(my_mutator)
        """
        if not callable(mutator):
            raise ValueError("mutator must be a callable")
        self.mutators.append(mutator)

    def load_mutator_plugin(self, plugin_path: str) -> None:
        """Load a custom mutator from an external Python plugin file.

        The file must define a top-level function `mutate(word: str) -> List[str]`.

        This enables a true plugin system where users can drop .py files
        with custom mutation logic (e.g. company-specific patterns, keyboard walks).

        Args:
            plugin_path: Path to the .py plugin file.

        Raises:
            FileNotFoundError, ImportError, AttributeError: On plugin load failure.
        """
        if not os.path.isfile(plugin_path):
            raise FileNotFoundError(f"Mutator plugin not found: {plugin_path}")

        module_name = f"wavebrute_plugin_{os.path.splitext(os.path.basename(plugin_path))[0]}"
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load spec for {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "mutate") or not callable(module.mutate):
            raise AttributeError(
                f"Plugin {plugin_path} must define a callable 'mutate(word)' function. "
                "Example:\n"
                "    def mutate(word: str) -> list[str]:\n"
                "        return [word + '!', word[::-1]]"
            )

        self.register_mutator(module.mutate)

    def from_ssid(self, ssid: str, size: int = 1500) -> List[str]:
        """Generate a targeted wordlist from an SSID with mutators applied.

        Base words are derived from the SSID, then all registered mutators
        (built-in + custom plugins) are applied to expand the list.
        """
        if not isinstance(ssid, str) or not ssid.strip():
            raise ValueError("ssid must be a non-empty string")
        ssid = ssid.strip()

        # Base generation (preserves original behaviour)
        base = []
        clean = ssid.lower().replace(" ", "").replace("-", "").replace("_", "")
        base.append(ssid)
        base.append(clean)
        base.append(clean.upper())
        base.append(clean.capitalize())
        base.append(clean + "123")
        base.append(clean + "2023")
        base.append("admin" + clean[:4] if len(clean) > 3 else "admin")
        base.append(clean[:6] + "wifi")

        # Add numeric variations
        for i in range(0, 100, 5):
            base.append(clean + str(i))
            base.append(str(i) + clean)

        # Apply all mutators to every base word
        expanded: List[str] = list(base)
        for word in base:
            for mutator in self.mutators:
                try:
                    mutations = mutator(word)
                    if isinstance(mutations, list):
                        expanded.extend(m for m in mutations if isinstance(m, str) and m)
                except Exception:  # protect against bad mutators
                    continue

        # Deduplicate while preserving order
        seen = {}
        unique = []
        for w in expanded:
            if w not in seen:
                seen[w] = True
                unique.append(w)

        # Trim or pad to requested size
        if len(unique) < size:
            for i in range(size - len(unique)):
                unique.append(f"{clean}{i:02d}")
        return unique[:size]

    def augment_with_ai(self, words: List[str], ssid: Optional[str] = None) -> List[str]:
        """Augment a wordlist with AI-generated pattern suggestions.

        Kept for backward compatibility with documentation.
        """
        ai_suggestions = generate_ai_suggestions(ssid or "network", max_suggestions=30)
        combined = list(dict.fromkeys(words + ai_suggestions))
        return combined[: len(words) * 2]  # reasonable expansion

    def save(
        self,
        output_path: str,
        words: Optional[List[str]] = None,
        ssid: Optional[str] = None,
        size: int = 1500,
    ) -> str:
        """Save wordlist to file. If words not provided, generates from ssid."""
        if words is None:
            words = self.from_ssid(ssid or "DefaultNet", size)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(words))

        return os.path.abspath(output_path)


def register_mutator(mutator: Callable[[str], List[str]]) -> Callable[[str], List[str]]:
    """Convenience decorator/function to register a mutator on a default generator.

    Primarily for standalone usage; Auditor users should prefer auditor.register_mutator().
    """
    if not hasattr(register_mutator, "_default_gen"):
        register_mutator._default_gen = WordlistGenerator()  # type: ignore[attr-defined]
    register_mutator._default_gen.register_mutator(mutator)  # type: ignore[attr-defined]
    return mutator


if __name__ == "__main__":
    generator = WordlistGenerator()
    wl = generator.from_ssid("Cafe_Rouge_FreeWiFi", size=20)
    print("Generated", len(wl), "words. First 5:", wl[:5])
    print("Plugin system ready. Use generator.load_mutator_plugin('my_mutator.py')")

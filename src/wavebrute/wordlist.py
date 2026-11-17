"""Targeted wordlist generation for WiFi auditing.

Generates smart, context-aware dictionaries based on SSID, common patterns,
and local 'AI' heuristics. Supports saving to disk for use with external
crackers like hashcat in authorized engagements.
"""

import random
from pathlib import Path
from typing import List, Optional

from .utils import generate_ai_suggestions


class WordlistGenerator:
    """Generates customized wordlists for password auditing simulations.

    Combines SSID-derived candidates, common password patterns, numeric
    suffixes, and AI-style suggestions. All operations are deterministic
    where possible for reproducible audits.
    """

    # Common base words and patterns likely to appear in weak WiFi passwords
    COMMON_BASES = [
        "password",
        "admin",
        "guest",
        "wifi",
        "network",
        "freewifi",
        "123456",
        "qwerty",
        "abc123",
        "letmein",
        "welcome",
        "test",
        "home",
        "office",
        "mobile",
        "iot",
        "camera",
        "printer",
    ]

    COMMON_SUFFIXES = [
        "",
        "123",
        "1234",
        "12345",
        "123456",
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
        "admin",
        "pass",
        "wifi",
        "home",
        "guest",
        "!",
        "??",
        "000",
        "111",
        "999",
    ]

    def __init__(self) -> None:
        """Initialize generator with static pattern lists."""

    def from_ssid(self, ssid: str, size: int = 1000) -> List[str]:
        """Generate a targeted wordlist from an SSID.

        Includes:
         - The SSID and cleaned versions
         - Common substitutions and appendages
         - AI-generated suggestions (from utils)
         - Variations with numbers and common suffixes

        Args:
            ssid: The network name to derive candidates from.
            size: Approximate number of entries to return.

        Returns:
            List of candidate passwords, prioritized by likelihood.

        Raises:
            ValueError: If ssid is empty or size is invalid.
        """
        if not isinstance(ssid, str) or len(ssid.strip()) == 0:
            raise ValueError("ssid must be a non-empty string")
        if not isinstance(size, int) or size < 10:
            raise ValueError("size must be an integer >= 10")

        ssid = ssid.strip()
        candidates: set[str] = set()

        # Base variations of the SSID itself
        candidates.add(ssid)
        candidates.add(ssid.lower())
        candidates.add(ssid.upper())

        clean_ssid = ssid.replace(" ", "").replace("-", "").replace("_", "")
        candidates.add(clean_ssid)
        candidates.add(clean_ssid.lower())

        # Add the common bases
        for base in self.COMMON_BASES:
            candidates.add(base)
            candidates.add(base.upper())
            candidates.add(base.capitalize())

        # SSID + common suffixes
        for suffix in self.COMMON_SUFFIXES:
            candidates.add(clean_ssid + suffix)
            candidates.add(clean_ssid.lower() + suffix)
            candidates.add(ssid + suffix)
            if suffix.isdigit():
                candidates.add(clean_ssid + suffix * 2)

        # Leetspeak variations
        leet_map = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$"}
        leeted = clean_ssid.lower()
        for k, v in leet_map.items():
            leeted = leeted.replace(k, v)
        candidates.add(leeted)
        candidates.add(leeted + "123")

        # Incorporate AI suggestions
        ai_suggestions = generate_ai_suggestions(ssid)
        candidates.update(ai_suggestions)

        # Add common passwords that often succeed in demos
        extra = [
            "password123",
            "admin123",
            "qwerty123",
            "abc123456",
            clean_ssid + "admin",
            clean_ssid + "123",
        ]
        candidates.update(extra)

        wordlist = list(candidates)

        # Fill up to desired size with systematic variations
        base_words = list(wordlist)
        i = 0
        while len(wordlist) < size and i < 500:
            for base in base_words[:5]:  # limit to avoid explosion
                for num in (str(i), str(i % 100).zfill(2), str(2020 + (i % 5))):
                    wordlist.append(base + num)
                    wordlist.append(base + num + "!")
                    if len(wordlist) >= size:
                        break
            i += 1

        # Deduplicate while preserving order of first appearance
        seen: set[str] = set()
        final_list: List[str] = []
        for w in wordlist:
            if w not in seen:
                seen.add(w)
                final_list.append(w)
            if len(final_list) >= size:
                break

        return final_list

    def augment_with_ai(self, patterns: List[str]) -> List[str]:
        """Expand an existing list of patterns with AI-inspired variations.

        Uses the same heuristics as generate_ai_suggestions but applied
        to a whole list of seed patterns.

        Args:
            patterns: Seed patterns (usually from SSID or previous list).

        Returns:
            Expanded list with additional candidates.

        Raises:
            ValueError: If patterns is not a list.
        """
        if not isinstance(patterns, list):
            raise ValueError("patterns must be a list of strings")

        if not patterns:
            return []

        augmented: set[str] = set(patterns)

        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            p = pattern.strip()
            if not p:
                continue
            augmented.update(generate_ai_suggestions(p))
            augmented.add(p + "123")
            augmented.add(p + "2023")
            augmented.add(p + "admin")
            augmented.add(p.capitalize() + "2024")
            # simple leets
            augmented.add(p.replace("a", "4").replace("e", "3"))

        return list(augmented)

    def save(
        self,
        path: str,
        wordlist: Optional[List[str]] = None,
        ssid: Optional[str] = None,
    ) -> str:
        """Save a wordlist to a text file (one password per line).

        If wordlist is not provided, it is generated from the ssid.

        Args:
            path: Destination file path.
            wordlist: Pre-generated list (optional).
            ssid: SSID to generate from if wordlist not supplied.

        Returns:
            Absolute path to the saved file.

        Raises:
            ValueError: On invalid arguments.
            OSError: If file cannot be written.
        """
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        if wordlist is None:
            if ssid is None:
                raise ValueError("Either wordlist or ssid must be provided to save()")
            if not isinstance(ssid, str) or not ssid.strip():
                raise ValueError("ssid must be a non-empty string")
            wordlist = self.from_ssid(ssid, size=2000)
        elif not isinstance(wordlist, list):
            raise ValueError("wordlist must be a list of strings")

        try:
            with path_obj.open("w", encoding="utf-8") as f:
                for entry in wordlist:
                    if isinstance(entry, str) and entry.strip():
                        f.write(entry.strip() + "\n")
        except OSError as exc:
            raise OSError(f"Failed to write wordlist to {path}: {exc}") from exc

        return str(path_obj.absolute())


if __name__ == "__main__":
    # Self demo
    gen = WordlistGenerator()
    wl = gen.from_ssid("MyHomeWiFi", size=50)
    print(f"Generated {len(wl)} candidates. First 5: {wl[:5]}")
    path = gen.save("demo_wordlist.txt", ssid="TestNet")
    print(f"Wordlist saved to: {path}")
    print("WordlistGenerator demo completed.")

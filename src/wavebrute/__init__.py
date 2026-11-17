"""WaveBrute — Ethical WiFi auditing toolkit.

A loud, neo-brutalist GUI application for responsible wireless security testing.
Supports live scanning (with mandatory consent), safe in-memory simulations,
targeted wordlist generation, handshake analysis, PDF reporting, and
Android deployment via Buildozer.

All live operations are guarded by an Ethics Guard. Simulation mode is
enabled by default for classrooms and training.

Public API:
    from wavebrute import Auditor, WordlistGenerator, ReportBuilder, ConsentManager
"""

__version__ = "0.1.0"

from .auditor import Auditor
from .wordlist import WordlistGenerator
from .report import ReportBuilder
from .ethics import ConsentManager

__all__ = [
    "Auditor",
    "WordlistGenerator",
    "ReportBuilder",
    "ConsentManager",
    "__version__",
]

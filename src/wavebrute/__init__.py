"""WaveBrute — Ethical WiFi auditing toolkit.

A loud, neo-brutalist GUI application for responsible wireless security testing.
Supports live scanning (with mandatory consent), safe in-memory simulations,
targeted wordlist generation, handshake analysis, PDF reporting, optional
hashcat .22000 export for real offline cracking, and Android deployment via
Buildozer.

All live operations are guarded by an Ethics Guard. Simulation mode is
enabled by default for classrooms and training. The new simulate_pmkid_attack()
and export_for_hashcat() demonstrate client-less RSN PMKID extraction,
cracking simulation, and direct interoperability with hashcat.

Public API:
    from wavebrute import Auditor, WordlistGenerator, ReportBuilder, ConsentManager

    auditor = Auditor(simulation_mode=True)
    auditor.simulate_pmkid_attack("MyNetwork")
    auditor.export_for_hashcat("MyNetwork")
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

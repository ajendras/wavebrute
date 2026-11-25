"""WaveBrute — Ethical WiFi auditing toolkit.

A loud, neo-brutalist GUI application for responsible wireless security testing.
Supports live scanning (with mandatory consent), safe in-memory simulations,
targeted wordlist generation, handshake analysis, multi-format reporting
(PDF/Markdown/HTML), optional hashcat .22000 export for real offline cracking,
and Android deployment via Buildozer.

All live operations are guarded by an Ethics Guard. Simulation mode is
enabled by default for classrooms and training. The new simulate_pmkid_attack()
and simulate_wps_attack() demonstrate client-less RSN PMKID extraction,
8-digit WPS PIN brute-force, cracking simulation, and direct interoperability
with hashcat and real-world attack vectors (with strong recommendations to
disable WPS).

The plugin system (register_mutator / load_mutator_plugin) lets users extend
wordlist generation with arbitrary Python logic or external .py plugin files.

The tiny on-device password prediction model (TinyPasswordModel) is trained
on a synthetic corpus of common weak passwords and SSID associations and is
bundled directly in the package (pure Python, no extra dependencies, works on
Android). It powers generate_ai_suggestions() and the new predict_passwords()
API.

The GUI now includes a dedicated CaptureScreen that supports capture file
upload (via Kivy FileChooser) and displays handshake analysis results. The
screen gracefully falls back to realistic simulation when the selected file
does not exist.

The new batch_audit() method allows auditing many networks in a single call
(running attack + optional PMKID + WPS + predictions simulations) and aggregates
results for easy one-command reporting.

Public API:
    from wavebrute import (
        Auditor, WordlistGenerator, ReportBuilder, ConsentManager,
        TinyPasswordModel, register_mutator
    )

    auditor = Auditor(simulation_mode=True)
    auditor.register_mutator(lambda w: [w + "2025"])
    auditor.simulate_pmkid_attack("MyNetwork")
    auditor.simulate_wps_attack("IoT-Devices")
    auditor.export_for_hashcat("MyNetwork")
    model = TinyPasswordModel().train()
    print(model.predict("CafeWiFi", 5))
    auditor.build_report(format="html")  # new: Markdown + HTML supported
    batch = auditor.batch_audit(["Net1", "Net2"], max_attempts=4000)
"""

__version__ = "0.1.0"

from .auditor import Auditor
from .wordlist import WordlistGenerator, register_mutator
from .report import ReportBuilder
from .ethics import ConsentManager
from .utils import TinyPasswordModel

__all__ = [
    "Auditor",
    "WordlistGenerator",
    "ReportBuilder",
    "ConsentManager",
    "TinyPasswordModel",
    "register_mutator",
    "__version__",
]

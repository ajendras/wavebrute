"""Android APK entry point for WaveBrute.

This file is used by Buildozer / python-for-android as the main script.
It ensures the src layout is on the Python path and launches the neo-brutalist Kivy GUI.
All functionality remains in simulation mode by default; live actions require explicit consent.
"""

import sys
from pathlib import Path

# Ensure the src package layout is importable on Android
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from wavebrute.gui.app import WaveBruteApp


if __name__ == "__main__":
    WaveBruteApp().run()

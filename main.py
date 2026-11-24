"""Android APK entrypoint for WaveBrute.

Defaults to dark theme on mobile for better battery life and high-contrast
brutalist aesthetics while preserving all existing functionality.
"""

from src.wavebrute.gui.app import WaveBruteApp

if __name__ == "__main__":
    # Buildozer expects the app to be instantiated here.
    # Dark theme is enabled by default on Android for optimal contrast.
    WaveBruteApp(simulation_mode=True, dark_theme=True).run()

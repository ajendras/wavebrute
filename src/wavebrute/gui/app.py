"""Main Kivy application for WaveBrute.

Implements the neo-brutalist UI exactly as specified: 3px black borders,
hard 6px offset shadows, flat bright blocks in #ff004d (magenta) and
#00ff9f (lime), chunky mono/grotesk typography, zero rounding, loud playful
layout. No blur, high contrast, responsive on mobile/desktop.

The app wires three screens (Scan, Attack, Report) that share a single
Auditor instance in safe simulation mode by default.
"""

import os
from typing import Optional

from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

from ..auditor import Auditor
from .screens import AttackScreen, ReportScreen, ScanScreen

# Neo-brutalist global config
Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("kivy", "window_icon", "wavebrute_icon.png")  # optional
Window.clearcolor = (0.98, 0.98, 0.05, 1.0)  # screaming yellow bg


class WaveBruteApp(App):
    """The loud neo-brutalist GUI entrypoint.

    Builds a ScreenManager containing ScanScreen, AttackScreen and
    ReportScreen. All screens share one Auditor(simulation_mode=True).
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = "WAVEBRUTE"
        self.auditor: Optional[Auditor] = None

    def build(self):
        """Assemble the brutalist UI and return the root ScreenManager."""
        if platform in ("android", "ios"):
            Window.maximize()

        self.auditor = Auditor(simulation_mode=True, interface="wlan0")

        sm = ScreenManager(transition="SlideTransition")
        sm.add_widget(ScanScreen(auditor=self.auditor, name="scan"))
        sm.add_widget(AttackScreen(auditor=self.auditor, name="attack"))
        sm.add_widget(ReportScreen(auditor=self.auditor, name="report"))

        # Start on the loudest screen
        sm.current = "scan"
        return sm

    def on_start(self):
        """Android permission hint (Buildozer will request these)."""
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions(
                [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_WIFI_STATE]
            )


if __name__ == "__main__":
    # Runnable demo
    WaveBruteApp().run()

from __future__ import annotations

from typing import Any

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import get_color_from_hex

from ..auditor import Auditor
from .screens import (
    AttackScreen,
    BrutalistButton,
    BrutalistLabel,
    CaptureScreen,
    ReportScreen,
    ScanScreen,
)


class WaveBruteApp(App):
    """Main application class with neo-brutalist UI and theme toggle."""

    def __init__(self, dark_theme: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dark_theme = dark_theme
        self.auditor = Auditor(simulation_mode=True)
        self.sm: ScreenManager | None = None
        self.header: BoxLayout | None = None
        self.theme_btn: BrutalistButton | None = None

    def build(self) -> BoxLayout:
        """Build UI with persistent brutalist header + ScreenManager."""
        self.sm = ScreenManager()

        self.sm.add_widget(ScanScreen(auditor=self.auditor))
        self.sm.add_widget(AttackScreen(auditor=self.auditor))
        self.sm.add_widget(CaptureScreen(auditor=self.auditor))
        self.sm.add_widget(ReportScreen(auditor=self.auditor))

        self.header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(80),
            padding=dp(16),
            spacing=dp(16),
        )

        title = BrutalistLabel(
            text="WAVEBRUTE",
            font_size=dp(32),
            color=get_color_from_hex("#00ff9f"),
            bold=True,
            size_hint_x=0.7,
        )

        self.theme_btn = BrutalistButton(
            text="LIGHT" if self.dark_theme else "DARK",
            size_hint_x=0.3,
            on_press=self.toggle_theme,
        )

        self.header.add_widget(title)
        self.header.add_widget(self.theme_btn)

        root = BoxLayout(orientation="vertical")
        root.add_widget(self.header)
        root.add_widget(self.sm)

        self.apply_theme()

        return root

    def toggle_theme(self, instance: Any) -> None:
        """Toggle dark/light theme and update UI."""
        self.dark_theme = not self.dark_theme
        if self.theme_btn:
            self.theme_btn.text = "LIGHT" if self.dark_theme else "DARK"
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the current theme to window and all screens."""
        if self.dark_theme:
            Window.clearcolor = get_color_from_hex("#111111")
        else:
            Window.clearcolor = get_color_from_hex("#f5f5f5")

        if self.sm:
            for screen in self.sm.screens:
                if hasattr(screen, "update_theme"):
                    screen.update_theme(self.dark_theme)

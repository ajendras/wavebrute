from __future__ import annotations

import os
from typing import Any

from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.utils import get_color_from_hex

from ..auditor import Auditor


class BrutalistButton(Button):
    """Neo-brutalist style button with thick borders."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex("#ff004d")
        self.color = get_color_from_hex("#ffffff")
        self.font_size = dp(18)
        self.size_hint_y = None
        self.height = dp(64)
        self.bold = True


class BrutalistLabel(Label):
    """Neo-brutalist label with thick border simulation via padding and color."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.color = get_color_from_hex("#00ff9f")
        self.font_size = dp(16)
        self.bold = True
        self.padding = (dp(8), dp(8))


class BaseScreen(Screen):
    """Base class for all screens with shared auditor and theme support."""

    is_dark = BooleanProperty(False)

    def __init__(self, auditor: Auditor | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor or Auditor(simulation_mode=True)
        self.build_ui()

    def build_ui(self) -> None:
        """Override in subclasses."""
        ...

    def update_theme(self, is_dark: bool) -> None:
        """Update theme colors (called by app toggle)."""
        self.is_dark = is_dark
        # In full implementation would update child widgets' colors


class ScanScreen(BaseScreen):
    """Screen for scanning networks."""

    def build_ui(self) -> None:
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        title = BrutalistLabel(
            text="SCAN NETWORKS",
            font_size=dp(28),
            size_hint_y=None,
            height=dp(60),
        )
        scan_btn = BrutalistButton(
            text="SCAN",
            on_press=self.perform_scan,
        )
        self.status = BrutalistLabel(text="Press SCAN to begin simulation")
        layout.add_widget(title)
        layout.add_widget(scan_btn)
        layout.add_widget(self.status)
        self.add_widget(layout)

    def perform_scan(self, instance: Any) -> None:
        networks = self.auditor.scan()
        self.status.text = f"Discovered {len(networks)} networks (simulation)"


class AttackScreen(BaseScreen):
    """Screen for attack simulations including PMKID and WPS."""

    def build_ui(self) -> None:
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        title = BrutalistLabel(
            text="ATTACK SIMULATIONS",
            font_size=dp(28),
            size_hint_y=None,
            height=dp(60),
        )
        attack_btn = BrutalistButton(
            text="SIMULATE BRUTEFORCE",
            on_press=self.run_attack,
        )
        pmkid_btn = BrutalistButton(
            text="SIMULATE PMKID",
            on_press=self.run_pmkid,
        )
        wps_btn = BrutalistButton(
            text="SIMULATE WPS",
            on_press=self.run_wps,
        )
        predict_btn = BrutalistButton(
            text="PREDICT PASSWORDS",
            on_press=self.run_predict,
        )
        self.status = BrutalistLabel(text="Select simulation type")
        layout.add_widget(title)
        layout.add_widget(attack_btn)
        layout.add_widget(pmkid_btn)
        layout.add_widget(wps_btn)
        layout.add_widget(predict_btn)
        layout.add_widget(self.status)
        self.add_widget(layout)

    def run_attack(self, instance: Any) -> None:
        result = self.auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
        self.status.text = f"Attack: {'SUCCESS' if result['success'] else 'failed'}"

    def run_pmkid(self, instance: Any) -> None:
        result = self.auditor.simulate_pmkid_attack("IoT-Devices")
        self.status.text = f"PMKID: {'SUCCESS' if result.get('success') else 'failed'}"

    def run_wps(self, instance: Any) -> None:
        result = self.auditor.simulate_wps_attack("IoT-Devices")
        self.status.text = f"WPS: {'SUCCESS' if result.get('success') else 'failed'}"

    def run_predict(self, instance: Any) -> None:
        preds = self.auditor.predict_passwords("Linksys-5G", 3)
        self.status.text = f"Predictions: {len(preds)} generated"


class CaptureScreen(BaseScreen):
    """Screen for uploading and analyzing capture files."""

    def build_ui(self) -> None:
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        title = BrutalistLabel(
            text="CAPTURE ANALYSIS",
            font_size=dp(28),
            size_hint_y=None,
            height=dp(60),
        )
        upload_btn = BrutalistButton(
            text="SELECT CAPTURE FILE",
            on_press=self.show_file_chooser,
        )
        self.status = BrutalistLabel(text="Ready for .cap upload")
        layout.add_widget(title)
        layout.add_widget(upload_btn)
        layout.add_widget(self.status)
        self.add_widget(layout)

    def show_file_chooser(self, instance: Any) -> None:
        content_layout = BoxLayout(orientation="vertical")
        self.filechooser = FileChooserListView(
            filters=["*.cap", "*.pcap", "*.pcapng"],
            size_hint=(1, 0.7),
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        cancel_btn = BrutalistButton(text="CANCEL", on_press=self.close_popup)
        analyze_btn = BrutalistButton(
            text="ANALYZE",
            on_press=self.do_analysis,
        )
        buttons.add_widget(cancel_btn)
        buttons.add_widget(analyze_btn)

        content_layout.add_widget(self.filechooser)
        content_layout.add_widget(buttons)

        self._popup = Popup(
            title="Choose Capture File",
            content=content_layout,
            size_hint=(0.9, 0.9),
        )
        self._popup.open()

    def close_popup(self, instance: Any = None) -> None:
        if hasattr(self, "_popup"):
            self._popup.dismiss()

    def do_analysis(self, instance: Any = None) -> None:
        selection = self.filechooser.selection
        capfile = selection[0] if selection else "demo.cap"
        try:
            analysis = self.auditor.analyze_handshake(capfile)
            self.status.text = (
                f"Analysis complete. Handshake: {analysis.get('has_handshake', False)}"
            )
        except (OSError, ValueError, RuntimeError) as exc:
            self.status.text = f"Error: {exc} (simulation used)"
        self.close_popup()


class ReportScreen(BaseScreen):
    """Screen for generating PDF/Markdown/HTML reports."""

    def build_ui(self) -> None:
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        title = BrutalistLabel(
            text="GENERATE REPORT",
            font_size=dp(28),
            size_hint_y=None,
            height=dp(60),
        )
        pdf_btn = BrutalistButton(
            text="GENERATE PDF REPORT",
            on_press=self.generate_pdf,
        )
        md_btn = BrutalistButton(
            text="GENERATE MARKDOWN",
            on_press=self.generate_md,
        )
        self.status = BrutalistLabel(text="Report will be saved to current dir")
        layout.add_widget(title)
        layout.add_widget(pdf_btn)
        layout.add_widget(md_btn)
        layout.add_widget(self.status)
        self.add_widget(layout)

    def generate_pdf(self, instance: Any) -> None:
        path = self.auditor.build_report(title="GUI Audit Report", format="pdf")
        self.status.text = f"PDF saved: {os.path.basename(path)}"

    def generate_md(self, instance: Any) -> None:
        path = self.auditor.build_report(title="GUI Audit Report", format="md")
        self.status.text = f"MD saved: {os.path.basename(path)}"

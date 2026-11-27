"""Kivy GUI screens for WaveBrute with neo-brutalist design.

Implements ScanScreen, AttackScreen, CaptureScreen, ReportScreen.
Supports dark theme toggle, uses dp for scalable Android/desktop UI,
thick borders, hard shadows. CaptureScreen uses FileChooser for .cap files.
All screens share an Auditor instance.
"""

import os
from typing import Any

from kivy.app import App as KivyApp
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import get_color_from_hex

from ..auditor import Auditor


class BrutalistButton(Button):
    """Neo-brutalist button with thick borders and high contrast."""

    is_dark = BooleanProperty(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(64)
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex("#00ff9f")
        self.bold = True
        self.update_style()

    def update_style(self) -> None:
        """Update colors based on dark/light theme."""
        if self.is_dark:
            self.color = get_color_from_hex("#00ff9f")
            border_color = get_color_from_hex("#ffff00")
        else:
            self.color = get_color_from_hex("#ff004d")
            border_color = get_color_from_hex("#00ff9f")
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*border_color)
            self.rect = Line(width=dp(4), rectangle=(self.x, self.y, self.width, self.height))
            Color(0, 0, 0, 0.6)
            self.shadow = Rectangle(pos=(self.x + dp(6), self.y - dp(6)), size=(self.width, self.height))

    def on_pos(self, *args: Any) -> None:
        self.update_style()

    def on_size(self, *args: Any) -> None:
        self.update_style()


class BrutalistLabel(Label):
    """Neo-brutalist label with thick borders for headers."""

    is_dark = BooleanProperty(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.font_size = dp(18)
        self.bold = True
        self.update_style()

    def update_style(self) -> None:
        if self.is_dark:
            self.color = get_color_from_hex("#ffff00")
        else:
            self.color = get_color_from_hex("#ff004d")


class BaseScreen(Screen):
    """Base for all screens with shared auditor and result display."""

    auditor = ObjectProperty(None)
    result_label = ObjectProperty(None)
    is_dark = BooleanProperty(False)

    def __init__(self, auditor: Auditor | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if auditor:
            self.auditor = auditor
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        self.add_widget(self.layout)
        self.build_ui()

    def build_ui(self) -> None:
        """Override in subclasses."""
        pass

    def update_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        for child in self.walk():
            if hasattr(child, "is_dark"):
                child.is_dark = is_dark
                if hasattr(child, "update_style"):
                    child.update_style()
        self.update_background()

    def update_background(self) -> None:
        with self.canvas.before:
            self.canvas.before.clear()
            if self.is_dark:
                Color(0.05, 0.05, 0.05, 1)
            else:
                Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def on_size(self, *args: Any) -> None:
        if hasattr(self, "bg_rect"):
            self.bg_rect.size = self.size
        if hasattr(self, "bg_rect") and hasattr(self, "pos"):
            self.bg_rect.pos = self.pos


class ScanScreen(BaseScreen):
    """Screen for scanning networks."""

    def build_ui(self) -> None:
        header = BrutalistLabel(text="SCAN NETWORKS", size_hint_y=None, height=dp(60))
        self.layout.add_widget(header)

        btn_scan = BrutalistButton(text="START SCAN")
        btn_scan.bind(on_press=self.do_scan)
        self.layout.add_widget(btn_scan)

        self.result_label = BrutalistLabel(
            text="Ready for scan. Press button to simulate or scan.", size_hint_y=0.6
        )
        self.layout.add_widget(self.result_label)

        btn_back = BrutalistButton(text="BACK TO MENU", size_hint_y=None, height=dp(50))
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

    def do_scan(self, instance: Any) -> None:
        try:
            networks = self.auditor.scan()
            text = f"Found {len(networks)} networks!\n"
            for net in networks[:3]:
                text += f"- {net['ssid']} ({net.get('encryption', 'OPEN')})\n"
            self.result_label.text = text
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"Scan error: {exc}"

    def go_back(self, instance: Any) -> None:
        self.manager.current = "menu"


class AttackScreen(BaseScreen):
    """Screen for attack simulations including PMKID and WPS."""

    def build_ui(self) -> None:
        header = BrutalistLabel(text="SIMULATE ATTACKS", size_hint_y=None, height=dp(60))
        self.layout.add_widget(header)

        self.ssid_input = Label(text="SSID: Cafe_Rouge_FreeWiFi")
        self.layout.add_widget(self.ssid_input)

        btn_attack = BrutalistButton(text="RUN BRUTE FORCE SIM")
        btn_attack.bind(on_press=self.run_attack)
        self.layout.add_widget(btn_attack)

        btn_pmkid = BrutalistButton(text="SIM PMKID ATTACK")
        btn_pmkid.bind(on_press=self.run_pmkid)
        self.layout.add_widget(btn_pmkid)

        btn_wps = BrutalistButton(text="SIM WPS ATTACK")
        btn_wps.bind(on_press=self.run_wps)
        self.layout.add_widget(btn_wps)

        self.result_label = BrutalistLabel(text="Select simulation to run...", size_hint_y=0.5)
        self.layout.add_widget(self.result_label)

        btn_back = BrutalistButton(text="BACK", size_hint_y=None, height=dp(50))
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

    def run_attack(self, instance: Any) -> None:
        try:
            result = self.auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=5000)
            self.result_label.text = (
                f"Attack on Cafe_Rouge_FreeWiFi:\n"
                f"Success: {result['success']}\n"
                f"Password: {result.get('password', 'Not found')}"
            )
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"Attack error: {exc}"

    def run_pmkid(self, instance: Any) -> None:
        try:
            result = self.auditor.simulate_pmkid_attack("IoT-Devices")
            self.result_label.text = f"PMKID Success: {result['success']}\nNotes: {result.get('notes', '')}"
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"PMKID error: {exc}"

    def run_wps(self, instance: Any) -> None:
        try:
            result = self.auditor.simulate_wps_attack("IoT-Devices")
            self.result_label.text = f"WPS Success: {result['success']}\nPIN: {result.get('pin', 'None')}"
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"WPS error: {exc}"

    def go_back(self, instance: Any) -> None:
        self.manager.current = "menu"


class CaptureScreen(BaseScreen):
    """Screen for uploading and analyzing handshake captures."""

    def build_ui(self) -> None:
        header = BrutalistLabel(text="CAPTURE ANALYSIS", size_hint_y=None, height=dp(60))
        self.layout.add_widget(header)

        btn_choose = BrutalistButton(text="CHOOSE CAPTURE FILE")
        btn_choose.bind(on_press=self.show_file_chooser)
        self.layout.add_widget(btn_choose)

        self.result_label = BrutalistLabel(
            text="Select a .cap/.pcap file for handshake analysis.\n"
            "Falls back to simulation if file missing.",
            size_hint_y=0.6,
        )
        self.layout.add_widget(self.result_label)

        btn_back = BrutalistButton(text="BACK", size_hint_y=None, height=dp(50))
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

    def show_file_chooser(self, instance: Any) -> None:
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        self.fc = FileChooserListView(
            path=".",
            filters=["*.cap", "*.pcap", "*.pcapng", "*.*"],
        )
        content.add_widget(self.fc)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        select_btn = BrutalistButton(text="ANALYZE SELECTED")
        select_btn.bind(on_press=self.load_selected)
        cancel_btn = BrutalistButton(text="CANCEL")
        cancel_btn.bind(on_press=self.close_popup)
        btn_box.add_widget(select_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)

        self.popup = Popup(title="Select Handshake Capture", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def close_popup(self, instance: Any = None) -> None:
        if hasattr(self, "popup"):
            self.popup.dismiss()

    def load_selected(self, instance: Any) -> None:
        if hasattr(self, "fc") and self.fc.selection:
            path = self.fc.selection[0]
            self.close_popup()
            self.analyze_file(path)
        else:
            self.close_popup()

    def analyze_file(self, path: str) -> None:
        try:
            analysis = self.auditor.analyze_handshake(path)
            crack_time = analysis.get("crack_time_estimate", "< 2 hours")
            self.result_label.text = (
                f"Crack estimate: {crack_time}\n"
                f"Handshake type: {analysis.get('handshake_type', '4-way')}\n"
                f"File: {os.path.basename(path)}"
            )
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"Analysis error: {exc}"

    def go_back(self, instance: Any) -> None:
        self.manager.current = "menu"


class ReportScreen(BaseScreen):
    """Screen for generating reports."""

    def build_ui(self) -> None:
        header = BrutalistLabel(text="GENERATE REPORT", size_hint_y=None, height=dp(60))
        self.layout.add_widget(header)

        btn_report = BrutalistButton(text="BUILD PDF REPORT")
        btn_report.bind(on_press=self.build_report)
        self.layout.add_widget(btn_report)

        btn_md = BrutalistButton(text="BUILD MARKDOWN REPORT")
        btn_md.bind(on_press=self.build_md_report)
        self.layout.add_widget(btn_md)

        self.result_label = BrutalistLabel(
            text="Press button to generate report from previous audits.", size_hint_y=0.6
        )
        self.layout.add_widget(self.result_label)

        btn_back = BrutalistButton(text="BACK", size_hint_y=None, height=dp(50))
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

    def build_report(self, instance: Any) -> None:
        try:
            path = self.auditor.build_report(title="WaveBrute Ethical Audit")
            self.result_label.text = f"Report saved successfully:\n{path}"
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"Report error: {exc}"

    def build_md_report(self, instance: Any) -> None:
        try:
            path = self.auditor.build_report(title="WaveBrute Ethical Audit", format="md")
            self.result_label.text = f"Markdown report saved:\n{path}"
        except (ValueError, PermissionError, RuntimeError, OSError, KeyError) as exc:
            self.result_label.text = f"Report error: {exc}"

    def go_back(self, instance: Any) -> None:
        self.manager.current = "menu"


class WaveBruteScreenManager(ScreenManager):
    """Manager for the neo-brutalist GUI."""

    def __init__(self, auditor: Auditor, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor
        self.is_dark = False

        self.add_widget(ScanScreen(auditor=auditor, name="scan"))
        self.add_widget(AttackScreen(auditor=auditor, name="attack"))
        self.add_widget(CaptureScreen(auditor=auditor, name="capture"))
        self.add_widget(ReportScreen(auditor=auditor, name="report"))


if __name__ == "__main__":
    # For quick widget testing

    from kivy.app import App as KivyApp

    from ..auditor import Auditor

    class TestApp(KivyApp):
        def build(self):
            auditor = Auditor(simulation_mode=True)
            sm = WaveBruteScreenManager(auditor=auditor)
            sm.current = "scan"
            return sm

    TestApp().run()

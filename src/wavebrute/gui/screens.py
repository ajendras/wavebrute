"""Neo-brutalist Kivy screens for WaveBrute.

Each screen follows the exact visual direction: thick 3dp black borders,
hard 6dp offset black shadows, flat #ff004d / #00ff9f colour blocks,
chunky monospace headings, zero radius, high contrast, playful loud copy.
All sizes now use kivy.metrics.dp so the UI scales correctly on Android
devices of any density while guaranteeing >=64dp touch targets.

All screens share an Auditor instance and demonstrate full pipeline:
live/safe scan, in-memory attack, PMKID simulation, PDF report generation.
"""

from typing import Any

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ..auditor import Auditor


class BrutalistButton(Button):
    """Reusable chunky neo-brutalist button.

    Now uses dp(64) minimum height for Android accessibility and scaling.
    3dp black border + 6dp hard shadow offset. Uses primary colours.
    """

    def __init__(self, accent: str = "#ff004d", **kwargs) -> None:
        super().__init__(**kwargs)
        self.accent = accent
        self.font_size = "22sp"
        self.bold = True
        self.color = (0, 0, 0, 1)
        self.background_color = (0, 0, 0, 0)  # we draw everything
        self.size_hint_y = None
        self.height = dp(64)  # improved touch target (Android recommendation >=48dp)
        self.padding = [dp(20), dp(12)]

        with self.canvas.before:
            # Shadow - hard 6dp offset
            Color(0.1, 0.1, 0.1, 1)
            self.shadow = Rectangle(
                pos=(self.x + dp(6), self.y - dp(6)), size=self.size
            )
            # Background
            Color(*self._to_color(accent))
            self.bg = Rectangle(pos=self.pos, size=self.size)
            # Border
            Color(0, 0, 0, 1)
            self.border = Line(width=dp(3), close=True)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

    @staticmethod
    def _to_color(hex_str: str):
        hex_str = hex_str.lstrip("#")
        return [int(hex_str[i : i + 2], 16) / 255.0 for i in range(0, 6, 2)] + [1.0]

    def _update_graphics(self, *args: Any) -> None:
        self.shadow.pos = (self.x + dp(6), self.y - dp(6))
        self.shadow.size = self.size
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class BrutalistLabel(Label):
    """Neo-brutalist label with thick border for headings and status."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = "18sp"
        self.bold = True
        self.color = (0, 0, 0, 1)
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(10), dp(10)]

        with self.canvas.before:
            Color(0.98, 0.98, 0.05, 1)  # yellow bg matching app background
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)
            self.border = Line(width=dp(3))

        self.bind(pos=self._update, size=self._update)

    def _update(self, *args: Any) -> None:
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class ScanScreen(Screen):
    auditor = ObjectProperty(None)

    def __init__(self, auditor: Auditor = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        self.add_widget(layout)

        # Header
        header = BrutalistLabel(
            text="WAVEBRUTE SCANNER",
            font_size="32sp",
            height=dp(90),
        )
        layout.add_widget(header)

        # Large touch target scan button
        scan_btn = BrutalistButton(text="SCAN NETWORKS", accent="#00ff9f")
        scan_btn.bind(on_release=self.do_scan)
        layout.add_widget(scan_btn)

        # Scrollable status
        scroll = ScrollView(size_hint=(1, 1))
        self.status = Label(
            text="Simulation mode ready.\nTap SCAN to discover networks.",
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(Window.width - dp(60), None),
        )
        self.status.bind(
            texture_size=lambda *x: setattr(
                self.status, "height", self.status.texture_size[1] + dp(30)
            )
        )
        scroll.add_widget(self.status)
        layout.add_widget(scroll)

        # Navigation
        nav_layout = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(15))
        to_attack = BrutalistButton(text="ATTACK", accent="#ff004d")
        to_attack.bind(on_release=lambda x: setattr(self.manager, "current", "attack"))
        to_report = BrutalistButton(text="REPORT", accent="#ff004d")
        to_report.bind(on_release=lambda x: setattr(self.manager, "current", "report"))
        nav_layout.add_widget(to_attack)
        nav_layout.add_widget(to_report)
        layout.add_widget(nav_layout)

    def do_scan(self, instance: Widget) -> None:
        if not self.auditor:
            self.status.text = "Auditor not available."
            return
        try:
            networks = self.auditor.scan()
            out = f"Found {len(networks)} networks (simulation):\n\n"
            for net in networks:
                out += f"• {net.get('ssid', 'Unknown')}\n  {net.get('encryption','?')} | {net.get('signal',0)} dBm\n\n"
            self.status.text = out
            Clock.schedule_once(
                lambda dt: setattr(
                    self.status, "text", self.status.text + "\nAudit logged."
                ),
                1.0,
            )
        except Exception as e:
            self.status.text = f"Error: {str(e)}\n\nAll operations are simulated."


class AttackScreen(Screen):
    auditor = ObjectProperty(None)

    def __init__(self, auditor: Auditor = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        self.add_widget(layout)

        header = BrutalistLabel(text="ATTACK SIMULATOR", font_size="32sp", height=dp(90))
        layout.add_widget(header)

        lbl = BrutalistLabel(text="TARGET SSID:", height=dp(40))
        layout.add_widget(lbl)

        self.ssid_input = TextInput(
            text="Cafe_Rouge_FreeWiFi",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size="18sp",
            padding=[dp(15), dp(15)],
        )
        layout.add_widget(self.ssid_input)

        brute_btn = BrutalistButton(text="BRUTE FORCE SIM", accent="#ff004d")
        brute_btn.bind(on_release=self.do_brute)
        layout.add_widget(brute_btn)

        pmkid_btn = BrutalistButton(text="PMKID SIMULATION", accent="#00ff9f")
        pmkid_btn.bind(on_release=self.do_pmkid)
        layout.add_widget(pmkid_btn)

        scroll = ScrollView(size_hint=(1, 1))
        self.result = Label(
            text="Results appear here...",
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(Window.width - dp(60), None),
        )
        self.result.bind(
            texture_size=lambda *x: setattr(
                self.result, "height", self.result.texture_size[1] + dp(30)
            )
        )
        scroll.add_widget(self.result)
        layout.add_widget(scroll)

        # Navigation
        nav = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(15))
        to_scan = BrutalistButton(text="SCAN", accent="#ff004d")
        to_scan.bind(on_release=lambda x: setattr(self.manager, "current", "scan"))
        to_report = BrutalistButton(text="REPORT", accent="#ff004d")
        to_report.bind(on_release=lambda x: setattr(self.manager, "current", "report"))
        nav.add_widget(to_scan)
        nav.add_widget(to_report)
        layout.add_widget(nav)

    def do_brute(self, instance: Widget) -> None:
        if not self.auditor:
            self.result.text = "No auditor."
            return
        ssid = self.ssid_input.text.strip() or "TestNet"
        try:
            res = self.auditor.simulate_attack(ssid, max_attempts=5000)
            self.result.text = (
                f"BRUTE FORCE SIMULATION\n"
                f"SSID: {res.get('ssid')}\n"
                f"Success: {res.get('success')}\n"
                f"Password: {res.get('password', 'Not found')}\n"
                f"Attempts: {res.get('attempts', 0)}\n\n"
                "Recommendations:\n"
                + "\n".join(res.get("recommendations", []))
            )
        except Exception as e:  # pylint: disable=broad-except
            self.result.text = f"Simulation error: {e}"

    def do_pmkid(self, instance: Widget) -> None:
        if not self.auditor:
            return
        ssid = self.ssid_input.text.strip() or "TestNet"
        try:
            res = self.auditor.simulate_pmkid_attack(ssid, max_attempts=5000)
            self.result.text = (
                f"PMKID SIMULATION\n"
                f"SSID: {res.get('ssid')}\n"
                f"Success: {res.get('success')}\n"
                f"Password: {res.get('password', 'N/A')}\n"
                f"Notes: {res.get('notes', '')}"
            )
        except Exception as e:  # pylint: disable=broad-except
            self.result.text = f"PMKID error: {e}"


class ReportScreen(Screen):
    auditor = ObjectProperty(None)

    def __init__(self, auditor: Auditor = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        self.add_widget(layout)

        header = BrutalistLabel(
            text="REPORT BUILDER", font_size="32sp", height=dp(90)
        )
        layout.add_widget(header)

        gen_btn = BrutalistButton(
            text="GENERATE PDF REPORT", accent="#00ff9f", height=dp(70)
        )
        gen_btn.bind(on_release=self.generate_report)
        layout.add_widget(gen_btn)

        self.report_status = Label(
            text="Click to generate a professional PDF report from simulation data.",
            size_hint_y=1,
            halign="center",
            valign="middle",
        )
        layout.add_widget(self.report_status)

        # Navigation
        nav = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(15))
        for name, label in (("scan", "SCAN"), ("attack", "ATTACK")):
            btn = BrutalistButton(text=label, accent="#ff004d")
            btn.bind(
                on_release=lambda x, target=name: setattr(self.manager, "current", target)
            )
            nav.add_widget(btn)
        layout.add_widget(nav)

    def generate_report(self, instance: Widget) -> None:
        if not self.auditor:
            self.report_status.text = "Auditor not initialized."
            return
        try:
            if not self.auditor.get_results():
                self.auditor.scan()
                self.auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
                self.auditor.simulate_pmkid_attack("IoT-Devices")
            path = self.auditor.build_report(title="Android Scaled Audit Report")
            self.report_status.text = (
                f"Report generated successfully!\n\nSaved to:\n{path}\n\n"
                "All data was simulated. Open with any PDF viewer."
            )
        except Exception as e:  # pylint: disable=broad-except
            self.report_status.text = f"Report generation failed:\n{str(e)}"


if __name__ == "__main__":
    # For quick testing of the UI components
    from kivy.app import App

    class TestApp(App):
        def build(self):
            aud = Auditor(simulation_mode=True)
            return ScanScreen(auditor=aud)

    TestApp().run()

"""Neo-brutalist Kivy screens for WaveBrute.

Each screen follows the exact visual direction: thick 3px black borders,
hard 6px offset black shadows, flat #ff004d / #00ff9f colour blocks,
chunky monospace headings, zero radius, high contrast, playful loud copy.
All screens share an Auditor instance and demonstrate full pipeline:
live/safe scan, in-memory attack, PDF report generation.
"""

from typing import Any, Dict, List

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ..auditor import Auditor
from ..ethics import ConsentManager


class BrutalistButton(Button):
    """Reusable chunky neo-brutalist button.

    3px black border + 6px hard shadow offset. Uses primary colours.
    """

    def __init__(self, accent: str = "#ff004d", **kwargs) -> None:
        super().__init__(**kwargs)
        self.accent = accent
        self.font_size = "22sp"
        self.bold = True
        self.color = (0, 0, 0, 1)
        self.background_color = (0, 0, 0, 0)  # we draw everything
        self.size_hint_y = None
        self.height = 80
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *_args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            # Hard shadow - offset black rectangle
            Color(0, 0, 0, 1)
            Rectangle(
                pos=(self.pos[0] + 6, self.pos[1] - 6),
                size=self.size,
            )
            # Thick black border + fill
            Color(0, 0, 0, 1)
            Line(
                width=3,
                rectangle=(
                    self.pos[0],
                    self.pos[1],
                    self.size[0],
                    self.size[1],
                ),
            )
            Color(*self._hex_to_rgba(self.accent))
            Rectangle(pos=self.pos, size=self.size)

    @staticmethod
    def _hex_to_rgba(hex_str: str) -> tuple[float, float, float, float]:
        h = hex_str.lstrip("#")
        return (
            int(h[0:2], 16) / 255,
            int(h[2:4], 16) / 255,
            int(h[4:6], 16) / 255,
            1.0,
        )


class BrutalistLabel(Label):
    """Chunky label with optional thick border."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = "28sp"
        self.bold = True
        self.color = (0, 0, 0, 1)
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *_args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 1)
            Line(
                width=3,
                rectangle=(
                    self.pos[0],
                    self.pos[1],
                    self.size[0],
                    self.size[1],
                ),
            )


class ScanScreen(Screen):
    """Live scanner screen with neo-brutalist list."""

    auditor = ObjectProperty(None)
    consent_manager = ObjectProperty(None)

    def __init__(self, auditor: Auditor, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor
        self.consent_manager = ConsentManager()

        root = BoxLayout(orientation="vertical", padding=15, spacing=15)

        # Header
        header = BrutalistLabel(
            text="WAVEBRUTE",
            size_hint_y=None,
            height=110,
            color=(1, 1, 1, 1),
        )
        with header.canvas.before:
            Color(1, 0, 0.3, 1)  # #ff004d
            Rectangle(pos=header.pos, size=header.size)
        root.add_widget(header)

        title = BrutalistLabel(
            text="NETWORK SCANNER",
            size_hint_y=None,
            height=60,
            font_size="38sp",
        )
        root.add_widget(title)

        self.status = Label(
            text="SIMULATION MODE — PRESS SCAN",
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),
            font_size="16sp",
        )
        root.add_widget(self.status)

        # Big scan button
        self.scan_btn = BrutalistButton(
            text="SCAN NETWORKS NOW", accent="#00ff9f", font_size="26sp"
        )
        self.scan_btn.bind(on_press=self._do_scan)
        root.add_widget(self.scan_btn)

        # Scrollable results
        scroll = ScrollView(size_hint=(1, 1))
        self.results_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=12, padding=10
        )
        self.results_box.bind(
            minimum_height=self.results_box.setter("height")
        )
        scroll.add_widget(self.results_box)
        root.add_widget(scroll)

        # Bottom nav
        nav = BoxLayout(size_hint_y=None, height=90, spacing=12)
        nav.add_widget(
            BrutalistButton(
                text="ATTACK", accent="#ff004d", font_size="18sp"
            ).__setattr__("on_press", lambda x: self.manager.current("attack"))
        )
        nav.add_widget(
            BrutalistButton(
                text="REPORT", accent="#ff004d", font_size="18sp"
            ).__setattr__("on_press", lambda x: self.manager.current("report"))
        )
        root.add_widget(nav)

        self.add_widget(root)

    def _do_scan(self, *_args: Any) -> None:
        self.scan_btn.text = "SCANNING..."
        self.results_box.clear_widgets()

        def run_scan(dt: float) -> None:
            try:
                networks = self.auditor.scan()
                self.status.text = f"FOUND {len(networks)} NETWORKS (SIM)"
                for net in networks:
                    row = BoxLayout(size_hint_y=None, height=68, spacing=8)
                    txt = (
                        f"{net.get('ssid','?')} | "
                        f"{net.get('encryption','OPEN')} | "
                        f"{net.get('signal',-50)} dBm"
                    )
                    lbl = BrutalistLabel(text=txt, font_size="15sp")
                    lbl.color = (0, 0, 0, 1)
                    row.add_widget(lbl)
                    self.results_box.add_widget(row)
            except Exception as exc:
                self.status.text = f"ERROR: {exc}"
            finally:
                self.scan_btn.text = "SCAN NETWORKS NOW"

        Clock.schedule_once(run_scan, 0.2)


class AttackScreen(Screen):
    """Simulated brute-force attack screen."""

    auditor = ObjectProperty(None)

    def __init__(self, auditor: Auditor, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor

        root = BoxLayout(orientation="vertical", padding=15, spacing=15)

        header = BrutalistLabel(
            text="BRUTE FORCE SIMULATOR",
            size_hint_y=None,
            height=90,
            font_size="36sp",
        )
        root.add_widget(header)

        self.ssid_input = TextInput(
            text="Cafe_Rouge_FreeWiFi",
            multiline=False,
            font_size="24sp",
            size_hint_y=None,
            height=60,
        )
        root.add_widget(self.ssid_input)

        self.attack_btn = BrutalistButton(
            text="RUN SAFE ATTACK", accent="#ff004d"
        )
        self.attack_btn.bind(on_press=self._run_attack)
        root.add_widget(self.attack_btn)

        self.result_label = Label(
            text="Attack result will appear here...",
            size_hint_y=0.6,
            font_size="18sp",
        )
        root.add_widget(self.result_label)

        # Bottom nav
        nav = BoxLayout(size_hint_y=None, height=90, spacing=12)
        for screen_name, label in [("scan", "SCAN"), ("report", "REPORT")]:
            btn = BrutalistButton(text=label, accent="#00ff9f", font_size="18sp")
            btn.bind(
                on_press=lambda _, name=screen_name: setattr(
                    self.manager, "current", name
                )
            )
            nav.add_widget(btn)
        root.add_widget(nav)

        self.add_widget(root)

    def _run_attack(self, *_args: Any) -> None:
        ssid = self.ssid_input.text.strip()
        if not ssid:
            self.result_label.text = "SSID CANNOT BE EMPTY"
            return

        self.attack_btn.text = "ATTACKING IN MEMORY..."
        self.result_label.text = "SIMULATING..."

        def attack_done(dt: float) -> None:
            try:
                result = self.auditor.simulate_attack(ssid, max_attempts=8000)
                if result.get("success"):
                    pwd = result.get("password", "???")
                    self.result_label.text = (
                        f"[b]CRACKED![/b]\n{pwd}\n"
                        f"{result['attempts']} attempts in "
                        f"{result['duration_seconds']}s"
                    )
                else:
                    self.result_label.text = "No password found in simulation."
            except Exception as exc:  # pylint: disable=broad-except
                self.result_label.text = f"ETHICS GUARD: {exc}"
            finally:
                self.attack_btn.text = "RUN SAFE ATTACK"

        Clock.schedule_once(attack_done, 0.6)


class ReportScreen(Screen):
    """PDF report generation screen."""

    auditor = ObjectProperty(None)

    def __init__(self, auditor: Auditor, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auditor = auditor

        root = BoxLayout(orientation="vertical", padding=15, spacing=15)

        header = BrutalistLabel(
            text="AUDIT REPORT", size_hint_y=None, height=90, font_size="36sp"
        )
        root.add_widget(header)

        self.info = Label(
            text="Press GENERATE to create PDF.\nAll prior results included.",
            size_hint_y=0.4,
            font_size="18sp",
        )
        root.add_widget(self.info)

        gen_btn = BrutalistButton(
            text="GENERATE PDF REPORT", accent="#00ff9f", font_size="26sp"
        )
        gen_btn.bind(on_press=self._generate_report)
        root.add_widget(gen_btn)

        self.path_label = Label(
            text="PDF will be saved in current directory",
            size_hint_y=0.3,
            font_size="15sp",
        )
        root.add_widget(self.path_label)

        # Bottom nav
        nav = BoxLayout(size_hint_y=None, height=90, spacing=12)
        for screen_name, label in [("scan", "SCAN"), ("attack", "ATTACK")]:
            btn = BrutalistButton(text=label, accent="#ff004d", font_size="18sp")
            btn.bind(
                on_press=lambda _, name=screen_name: setattr(
                    self.manager, "current", name
                )
            )
            nav.add_widget(btn)
        root.add_widget(nav)

        self.add_widget(root)

    def _generate_report(self, *_args: Any) -> None:
        try:
            path = self.auditor.build_report(
                title="WaveBrute Neo-Brutalist Audit"
            )
            self.path_label.text = f"SAVED TO:\n{path}"
            self.info.text = "REPORT GENERATED SUCCESSFULLY\n(open it with any PDF viewer)"
        except Exception as exc:  # pylint: disable=broad-except
            self.info.text = f"REPORT ERROR:\n{exc}"


if __name__ == "__main__":
    # Demo the screens directly
    from kivy.app import App
    from ..auditor import Auditor

    class DemoApp(App):
        def build(self):
            auditor = Auditor(simulation_mode=True)
            return ScanScreen(auditor=auditor)

    DemoApp().run()

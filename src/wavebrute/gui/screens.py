"""Neo-brutalist GUI screens for WaveBrute.

Defines ScanScreen, AttackScreen, CaptureScreen (new) and ReportScreen.
Uses custom Brutalist* widgets with thick borders, hard offset shadows
and screaming colors. All measurements in dp for correct scaling on
desktop and Android. CaptureScreen implements file upload via a
FileChooserListView popup (filtered to capture extensions) and runs
Auditor.analyze_handshake(), displaying results with automatic
simulation fallback.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line


class BrutalistWidgetMixin:
    """Mixin to apply neo-brutalist styling: thick black borders + hard shadow."""

    def apply_brutalist_style(self, base_color=(1, 0.0078, 0.3, 1), text_color=(0.98, 0.98, 0.05, 1)):
        self.background_color = (0, 0, 0, 0)  # transparent for canvas drawing
        self.color = text_color
        self.font_size = dp(18)
        self.bold = True
        self.padding = dp(12)
        with self.canvas.before:
            # Hard shadow (offset)
            Color(0.15, 0.15, 0.15, 1)
            self.shadow = Rectangle(pos=(self.x + dp(8), self.y - dp(8)), size=self.size)
            # Main fill
            Color(*base_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            # Thick border
            Color(0, 0, 0, 1)
            self.border_line = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=dp(4)
            )
        self.bind(pos=self._update_rects, size=self._update_rects)

    def _update_rects(self, *args):
        self.shadow.pos = (self.x + dp(6), self.y - dp(6))
        self.shadow.size = (self.width, self.height)
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rectangle = (self.x, self.y, self.width, self.height)


class BrutalistLabel(Label, BrutalistWidgetMixin):
    """Brutalist label with thick border and shadow."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(52)
        self.apply_brutalist_style(
            base_color=(0.98, 0.98, 0.0, 1), text_color=(0, 0, 0, 1)
        )  # yellow blocks, black text for labels


class BrutalistButton(Button, BrutalistWidgetMixin):
    """Chunky brutalist button. Minimum 64dp for touch targets."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(72)
        self.apply_brutalist_style(
            base_color=(1.0, 0.0078, 0.3019, 1), text_color=(0.98, 0.98, 0.05, 1)
        )  # magenta button, lime-yellow text


class BaseScreen(Screen):
    """Common base for all screens with header and bottom navigation."""

    def __init__(self, auditor, **kwargs):
        super().__init__(**kwargs)
        self.auditor = auditor
        self.layout = BoxLayout(orientation="vertical", spacing=dp(15), padding=dp(20))
        self.add_widget(self.layout)

        # Loud header
        header = BrutalistLabel(
            text=self.name.upper(), font_size=dp(32), height=dp(90)
        )
        self.layout.add_widget(header)

    def add_nav_buttons(self):
        """Add chunky navigation bar to switch between the four screens."""
        nav_layout = GridLayout(cols=4, size_hint_y=None, height=dp(80), spacing=dp(8))
        for screen_name, text in [
            ("scan", "SCAN"),
            ("attack", "ATTACK"),
            ("capture", "CAPTURE"),
            ("report", "REPORT"),
        ]:
            btn = BrutalistButton(text=text, height=dp(64))
            btn.bind(
                on_press=lambda x, s=screen_name: setattr(self.manager, "current", s)
            )
            nav_layout.add_widget(btn)
        self.layout.add_widget(nav_layout)


class ScanScreen(BaseScreen):
    """Screen for network scanning."""

    def __init__(self, auditor, **kwargs):
        super().__init__(auditor, name="scan", **kwargs)
        self.result_scroll = ScrollView(size_hint=(1, 1))
        self.results_label = Label(
            text="Press SCAN to detect networks (simulation mode).",
            size_hint_y=None,
            height=dp(420),
            text_size=(dp(420), None),
        )
        self.result_scroll.add_widget(self.results_label)
        self.layout.add_widget(self.result_scroll)

        scan_btn = BrutalistButton(text="SCAN NETWORKS")
        scan_btn.bind(on_press=self.do_scan)
        self.layout.add_widget(scan_btn)

        self.add_nav_buttons()

    def do_scan(self, instance):
        try:
            nets = self.auditor.scan()
            text = "NETWORKS FOUND (SIMULATION):\n\n"
            for net in nets:
                text += (
                    f"• {net.get('ssid', 'Unknown')} | "
                    f"{net.get('encryption', 'OPEN')} | "
                    f"{net.get('signal', -50)} dBm\n"
                )
            self.results_label.text = text
        except Exception as e:
            self.results_label.text = f"Scan error (simulation fallback):\n{str(e)}"


class AttackScreen(BaseScreen):
    """Screen for attack simulations including PMKID."""

    def __init__(self, auditor, **kwargs):
        super().__init__(auditor, name="attack", **kwargs)

        self.ssid_input = TextInput(
            text="Cafe_Rouge_FreeWiFi",
            multiline=False,
            size_hint_y=None,
            height=dp(64),
            font_size=dp(18),
        )
        self.layout.add_widget(BrutalistLabel(text="Target SSID"))
        self.layout.add_widget(self.ssid_input)

        attack_btn = BrutalistButton(text="SIMULATE BRUTE FORCE")
        attack_btn.bind(on_press=self.do_attack)
        self.layout.add_widget(attack_btn)

        pmkid_btn = BrutalistButton(text="SIMULATE PMKID ATTACK")
        pmkid_btn.bind(on_press=self.do_pmkid)
        self.layout.add_widget(pmkid_btn)

        self.result_scroll = ScrollView(size_hint=(1, 1))
        self.results_label = Label(
            text="Attack results will appear here...",
            size_hint_y=None,
            height=dp(340),
            text_size=(dp(400), None),
        )
        self.result_scroll.add_widget(self.results_label)
        self.layout.add_widget(self.result_scroll)

        self.add_nav_buttons()

    def do_attack(self, instance):
        ssid = self.ssid_input.text.strip()
        if not ssid:
            self.results_label.text = "ERROR: SSID cannot be empty."
            return
        try:
            res = self.auditor.simulate_attack(ssid, max_attempts=6000)
            self.results_label.text = self._format_result(res)
        except Exception as e:
            self.results_label.text = f"SIMULATION ERROR:\n{str(e)}"

    def do_pmkid(self, instance):
        ssid = self.ssid_input.text.strip()
        if not ssid:
            self.results_label.text = "ERROR: SSID cannot be empty."
            return
        try:
            res = self.auditor.simulate_pmkid_attack(ssid, max_attempts=6000)
            self.results_label.text = self._format_result(res)
        except Exception as e:
            self.results_label.text = f"SIMULATION ERROR:\n{str(e)}"

    def _format_result(self, res):
        lines = ["=== SIMULATION RESULT ===", ""]
        for k, v in res.items():
            if isinstance(v, (list, dict)):
                continue
            lines.append(f"{k.replace('_', ' ').upper()}: {v}")
        return "\n".join(lines)


class CaptureScreen(BaseScreen):
    """New screen: capture file upload and analysis.

    Provides a file browser (FileChooserListView in a Popup) limited to
    common capture extensions. Calls auditor.analyze_handshake() and
    displays rich results. Uses simulation automatically when the file
    is missing or cannot be parsed.
    """

    def __init__(self, auditor, **kwargs):
        super().__init__(auditor, name="capture", **kwargs)

        self.layout.add_widget(
            BrutalistLabel(
                text="CAPTURE FILE UPLOAD & ANALYSIS",
                font_size=dp(26),
                height=dp(70),
            )
        )

        # File path row
        file_row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(70), spacing=dp(12)
        )
        self.file_input = TextInput(
            text="demo.cap",
            multiline=False,
            size_hint_x=0.75,
            font_size=dp(17),
        )
        file_row.add_widget(self.file_input)

        browse_btn = BrutalistButton(text="BROWSE", size_hint_x=0.25)
        browse_btn.bind(on_press=self.show_file_chooser)
        file_row.add_widget(browse_btn)

        self.layout.add_widget(BrutalistLabel(text="Capture file (.cap/.pcap)"))
        self.layout.add_widget(file_row)

        analyze_btn = BrutalistButton(text="ANALYZE CAPTURE")
        analyze_btn.bind(on_press=self.analyze_file)
        self.layout.add_widget(analyze_btn)

        self.result_scroll = ScrollView(size_hint=(1, 1))
        self.result_label = Label(
            text=(
                "Select or enter a capture file path.\n"
                "The analyzer will use realistic simulation if the file is not found.\n\n"
                "Ready for upload & analysis."
            ),
            size_hint_y=None,
            height=dp(420),
            text_size=(dp(420), None),
        )
        self.result_scroll.add_widget(self.result_label)
        self.layout.add_widget(self.result_scroll)

        self.add_nav_buttons()

    def show_file_chooser(self, instance):
        """Open a modal file chooser limited to capture files."""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        self.file_chooser = FileChooserListView(
            path=".",
            filters=["*.cap", "*.pcap", "*.pcapng"],
            size_hint=(1, 0.85),
        )
        content.add_widget(self.file_chooser)

        btn_row = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(15))
        select_btn = BrutalistButton(text="SELECT FILE")
        cancel_btn = BrutalistButton(text="CANCEL")
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        self.popup = Popup(
            title="Select Capture File",
            content=content,
            size_hint=(0.9, 0.85),
        )
        select_btn.bind(on_press=self._on_file_selected)
        cancel_btn.bind(on_press=self.popup.dismiss)
        self.popup.open()

    def _on_file_selected(self, instance):
        if self.file_chooser.selection:
            self.file_input.text = self.file_chooser.selection[0]
        self.popup.dismiss()

    def analyze_file(self, instance):
        """Perform handshake analysis (simulation fallback if needed)."""
        cap_path = self.file_input.text.strip()
        if not cap_path:
            self.result_label.text = "ERROR: Please select or enter a capture file path."
            return

        try:
            analysis = self.auditor.analyze_handshake(cap_path)
            output = "=== CAPTURE ANALYSIS RESULTS ===\n\n"
            keys = [
                "file",
                "has_handshake",
                "handshake_type",
                "crackable",
                "crack_time_estimate",
                "simulation",
                "ap_mac",
                "client_mac",
                "notes",
            ]
            for key in keys:
                if key in analysis:
                    val = analysis[key]
                    label = key.replace("_", " ").upper()
                    output += f"{label}:\n{val}\n\n"
            self.result_label.text = output
        except Exception as exc:
            self.result_label.text = (
                f"ANALYSIS ERROR:\n{str(exc)}\n\n"
                "Note: Simulation mode was used. Provide a valid .cap file for real parsing."
            )


class ReportScreen(BaseScreen):
    """Screen for generating reports."""

    def __init__(self, auditor, **kwargs):
        super().__init__(auditor, name="report", **kwargs)

        self.title_input = TextInput(
            text="WaveBrute Ethical Audit",
            multiline=False,
            size_hint_y=None,
            height=dp(64),
            font_size=dp(18),
        )
        self.layout.add_widget(BrutalistLabel(text="Report Title"))
        self.layout.add_widget(self.title_input)

        pdf_btn = BrutalistButton(text="GENERATE PDF REPORT")
        pdf_btn.bind(on_press=lambda x: self.build_report("pdf"))
        self.layout.add_widget(pdf_btn)

        html_btn = BrutalistButton(text="GENERATE HTML REPORT")
        html_btn.bind(on_press=lambda x: self.build_report("html"))
        self.layout.add_widget(html_btn)

        self.result_scroll = ScrollView(size_hint=(1, 1))
        self.result_label = Label(
            text="Report output will be shown here.",
            size_hint_y=None,
            height=dp(300),
            text_size=(dp(400), None),
        )
        self.result_scroll.add_widget(self.result_label)
        self.layout.add_widget(self.result_scroll)

        self.add_nav_buttons()

    def build_report(self, fmt: str):
        try:
            title = self.title_input.text.strip() or "WaveBrute Ethical Audit Report"
            path = self.auditor.build_report(title=title, format=fmt)
            self.result_label.text = (
                f"REPORT GENERATED SUCCESSFULLY\n\n"
                f"Format: {fmt.upper()}\n"
                f"Location:\n{path}\n\n"
                "All actions were performed in simulation mode."
            )
        except Exception as e:
            self.result_label.text = f"REPORT ERROR:\n{str(e)}"

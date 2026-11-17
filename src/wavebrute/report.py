"""PDF report generation for WaveBrute audits.

Uses ReportLab for a loud neo-brutalist PDF (thick black rules, #ff004d
and #00ff9f accents, chunky headings). Jinja2 is used to render a text
summary that is then laid out professionally in the PDF.

All methods validate inputs strictly. The resulting PDF includes:
- Header with brutalist branding
- Summary statistics
- Per-result sections with tables
- Ethics statement and recommendations
- Timestamped footer
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .utils import validate_mac


class ReportBuilder:
    """Builds professional PDF audit reports from Auditor results.

    The classmethod ``from_results`` is the preferred entry point.
    ``render_template`` produces a textual summary; ``to_pdf`` produces
    the final styled PDF with neo-brutalist visual language.
    """

    TEMPLATE = """
    <h1>{{ title }}</h1>
    <p><b>Date:</b> {{ date }}</p>
    <h2>Summary</h2>
    <p>{{ summary }}</p>
    <h2>Findings ({{ results|length }})</h2>
    {% for r in results %}
    <h3>{{ loop.index }}. {{ r.get('ssid', r.get('type', 'Result')) }}</h3>
    <ul>
    {% for k, v in r.items() %}
        {% if k not in ['recommendations', 'timestamp'] %}
        <li><b>{{ k }}:</b> {{ v }}</li>
        {% endif %}
    {% endfor %}
    </ul>
    {% endfor %}
    <h2>Ethics & Recommendations</h2>
    <p>ALL OPERATIONS WERE PERFORMED UNDER EXPLICIT CONSENT OR IN SAFE SIMULATION MODE.</p>
    """

    def __init__(self, results: List[Dict[str, Any]]) -> None:
        """Private constructor. Use ``from_results`` instead."""
        if not isinstance(results, list):
            raise ValueError("results must be a list of dicts")
        self.results = results
        self.template = Template(self.TEMPLATE)

    @classmethod
    def from_results(cls, results: List[Dict[str, Any]]) -> "ReportBuilder":
        """Factory method used by Auditor.build_report()."""
        if not isinstance(results, list):
            raise ValueError("ReportBuilder.from_results expects a list")
        return cls(results)

    def render_template(self) -> str:
        """Render results into a Jinja2 text summary (used internally)."""
        summary = (
            f"WaveBrute audit completed with {len(self.results)} finding(s). "
            f"Simulation mode active in {sum(1 for r in self.results if r.get('simulation', False))} result(s)."
        )
        context = {
            "title": "WaveBrute Ethical Audit Report",
            "date": datetime.now().strftime("%d %b %Y at %H:%M"),
            "summary": summary,
            "results": self.results,
        }
        return self.template.render(**context)

    def to_pdf(
        self,
        title: str = "WaveBrute Ethical Audit Report",
        output_path: str = "",
    ) -> str:
        """Generate a neo-brutalist PDF report.

        Thick black borders, hard shadows simulated by offset rectangles,
        bright accent colours (#ff004d, #00ff9f), chunky headings.

        Args:
            title: Report title (appears on cover).
            output_path: Destination path. If empty, auto-generates.

        Returns:
            Absolute path to the written PDF.

        Raises:
            ValueError: If results list is empty or arguments are malformed.
            OSError: If PDF cannot be written.
        """
        if not self.results:
            raise ValueError(
                "No audit results to report. Call Auditor.scan(), "
                "simulate_attack(), or analyze_handshake() first."
            )
        if not isinstance(title, str) or not title.strip():
            title = "WaveBrute Ethical Audit Report"
        if not isinstance(output_path, str):
            raise ValueError("output_path must be a string")

        if not output_path.strip():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wavebrute_report_{ts}.pdf"

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        brutal_title = ParagraphStyle(
            "BrutalTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=32,
            textColor=colors.HexColor("#ff004d"),
            backColor=colors.HexColor("#00ff9f"),
            borderWidth=6,
            borderColor=colors.black,
            borderPadding=(12, 12, 12, 12),
            alignment=1,
            spaceAfter=30,
        )

        heading = ParagraphStyle(
            "BrutalHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.black,
            backColor=colors.HexColor("#ff004d"),
            borderWidth=3,
            borderColor=colors.black,
            borderPadding=(8, 8, 8, 8),
            spaceBefore=20,
            spaceAfter=12,
        )

        normal = styles["Normal"]
        normal.fontName = "Helvetica"
        normal.fontSize = 11
        normal.spaceAfter = 8

        elements = []

        # Header with hard shadow simulation via offset text
        elements.append(Paragraph(title, brutal_title))
        elements.append(Spacer(1, 0.2 * inch))

        # Summary
        elements.append(Paragraph("EXECUTIVE SUMMARY", heading))
        summary_text = self.render_template().split("<h2>Findings")[0]
        for para in summary_text.split("\n"):
            if para.strip():
                elements.append(Paragraph(para.strip(), normal))

        elements.append(Spacer(1, 0.3 * inch))

        # Detailed findings
        elements.append(Paragraph("DETAILED FINDINGS", heading))
        for idx, result in enumerate(self.results, 1):
            ssid = result.get("ssid") or result.get("type", f"Finding {idx}")
            elements.append(
                Paragraph(f"{idx}. {ssid}", heading)
            )

            data = [["KEY", "VALUE"]]
            for k, v in result.items():
                if k in ("recommendations", "timestamp", "ai_suggestions_used"):
                    continue
                if isinstance(v, bool):
                    v = "YES" if v else "NO"
                elif isinstance(v, (list, dict)):
                    v = str(v)[:60] + "..."
                data.append([str(k).upper(), str(v)])

            t = Table(data, colWidths=[110, 320])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00ff9f")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("BOX", (0, 0), (-1, -1), 4, colors.black),
                        ("GRID", (0, 0), (-1, -1), 2, colors.black),
                        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#ffeecc")),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ]
                )
            )
            elements.append(t)
            elements.append(Spacer(1, 0.2 * inch))

        # Recommendations block
        elements.append(Paragraph("RECOMMENDATIONS & ETHICS STATEMENT", heading))
        recs = [
            "• Use passwords longer than 20 characters with full entropy.",
            "• Prefer WPA3; disable WPS and guest networks.",
            "• Monitor for rogue access points regularly.",
            "• This tool was used in simulation mode or with explicit consent.",
            "• Unauthorised wireless testing is illegal in most jurisdictions.",
            "• Always delete captures after an authorised engagement.",
        ]
        for rec in recs:
            elements.append(Paragraph(rec, normal))

        elements.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            "Footer",
            parent=normal,
            fontSize=9,
            textColor=colors.gray,
            alignment=1,
        )
        elements.append(
            Paragraph(
                f"Generated by WaveBrute v0.1.0 on {datetime.now().isoformat()} • "
                "ETHICAL USE ONLY",
                footer_style,
            )
        )

        try:
            doc.build(elements)
        except Exception as exc:
            raise OSError(f"Failed to write PDF to {output_path}: {exc}") from exc

        return os.path.abspath(output_path)


if __name__ == "__main__":
    # Self-contained runnable demo
    from .auditor import Auditor

    print("=== WaveBrute ReportBuilder Demo ===")
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
    auditor.analyze_handshake("demo.cap")  # will simulate

    builder = ReportBuilder.from_results(auditor.get_results())
    pdf_path = builder.to_pdf("Demo Audit Report")
    print(f"PDF report written to: {pdf_path}")
    print("ReportBuilder demo completed successfully.")

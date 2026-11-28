"""Report generation for WaveBrute audits.

Supports PDF (with ReportLab), Markdown and HTML outputs with neo-brutalist styling for HTML.
Uses Jinja2 for templating.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import jinja2
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportBuilder:
    """Builds professional audit reports from Auditor results."""

    @classmethod
    def from_results(cls, results: list[dict[str, Any]]) -> "ReportBuilder":
        """Create builder from list of audit result dicts."""
        return cls(results)

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=True,
        )

    def to_pdf(
        self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.pdf"
    ) -> str:
        """Generate PDF report using ReportLab with brutalist styling."""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=24,
            textColor=colors.HexColor("#ff004d"),
            spaceAfter=30,
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))

        for result in self.results:
            if isinstance(result, dict):
                text = f"<b>{result.get('type', 'Result')}:</b> {result.get('ssid', 'N/A')}"
                if result.get("success"):
                    text += " - SUCCESS"
                story.append(Paragraph(text, styles["Normal"]))
                story.append(Spacer(1, 12))

        data = [["Type", "SSID", "Success"]]
        for r in self.results[:5]:
            data.append(
                [
                    str(r.get("type", "N/A"))[:10],
                    str(r.get("ssid", "N/A"))[:15],
                    str(r.get("success", False)),
                ]
            )
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff004d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(table)

        doc.build(story)
        return os.path.abspath(output_path)

    def to_markdown(
        self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.md"
    ) -> str:
        """Generate Markdown report."""
        content = f"# {title}\n\n"
        content += f"Generated: {datetime.now().isoformat()}\n\n"
        content += "## Findings\n\n"
        for result in self.results:
            content += f"- **{result.get('type', 'Unknown')}** for {result.get('ssid', 'N/A')}: "
            content += f"Success = {result.get('success', 'N/A')}\n"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return os.path.abspath(output_path)

    def to_html(
        self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.html"
    ) -> str:
        """Generate HTML report with neo-brutalist CSS."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ background: #1a1a1a; color: #00ff9f; font-family: monospace; }}
        h1 {{ color: #ff004d; border-bottom: 6px solid #ffff00; }}
        .brutalist {{ border: 4px solid #ffff00; padding: 20px; margin: 10px; background: #2a2a2a; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated on {datetime.now().isoformat()}</p>
"""
        for result in self.results:
            html += f'    <div class="brutalist"><h2>{result.get("type", "Result")}</h2><p>SSID: {result.get("ssid", "N/A")}<br>Success: {result.get("success", False)}</p></div>\n'
        html += "</body></html>"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return os.path.abspath(output_path)


if __name__ == "__main__":
    builder = ReportBuilder.from_results([])
    print("ReportBuilder ready.")

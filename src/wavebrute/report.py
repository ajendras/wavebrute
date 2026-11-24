import os
from pathlib import Path
from typing import Any

import jinja2


class ReportBuilder:
    """Builds professional audit reports in PDF, Markdown or HTML.

    Uses ReportLab for PDF with graceful fallback to Markdown.
    HTML includes inline neo-brutalist styling.
    """

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results

    @staticmethod
    def from_results(results: list[dict[str, Any]]) -> "ReportBuilder":
        """Factory from audit results list."""
        if not isinstance(results, list):
            raise TypeError("results must be a list of dicts")
        return ReportBuilder(results)

    def render_template(self, title: str, fmt: str = "md") -> str:
        """Render results using a Jinja2 template."""
        template_str = """
# {{ title }}

**Generated:** {{ timestamp }}
**Networks audited:** {{ networks }}

## Findings
{% for r in results %}
- **{{ r.get('type', 'result') }}** on *{{ r.get('ssid', 'N/A') }}* — success: {{ r.get('success', 'N/A') }}
{% endfor %}

## Recommendations
* Use 20+ character random passwords
* Prefer WPA3
* Disable WPS and guest networks
* Monitor with tools like WaveBrute
"""
        tmpl = jinja2.Template(template_str)
        return tmpl.render(
            title=title,
            timestamp="2025-01-01T00:00:00",
            networks=len(self.results),
            results=self.results,
        )

    def to_markdown(self, title: str = "WaveBrute Ethical Audit Report", output_path: str | None = None) -> str:
        """Write Markdown report (GitHub-friendly)."""
        if output_path is None:
            output_path = "wavebrute_report.md"
        content = self.render_template(title, "md")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return os.path.abspath(output_path)

    def to_html(self, title: str = "WaveBrute Ethical Audit Report", output_path: str | None = None) -> str:
        """Write HTML report with neo-brutalist styling."""
        if output_path is None:
            output_path = "wavebrute_report.html"
        content = self.render_template(title, "html")
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ background:#111; color:#0f0; font-family:monospace; padding:40px; }}
        h1 {{ border:8px solid #ff004d; padding:30px; background:#222; color:#00ff9f; }}
        pre {{ background:#1a1a1a; padding:20px; border:4px solid #ffff00; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <pre>{content}</pre>
</body>
</html>"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return os.path.abspath(output_path)

    def to_pdf(self, title: str = "WaveBrute Ethical Audit Report", output_path: str | None = None) -> str:
        """Generate PDF via ReportLab; falls back to Markdown on any failure.

        The md_path variable is now used (returned) so F841 is resolved.
        """
        if output_path is None:
            output_path = "wavebrute_report.pdf"

        try:
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

            doc = SimpleDocTemplate(output_path)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph(f"<font color='#ff004d'>{title}</font>", styles["Title"]))
            elements.append(Spacer(1, 30))

            for result in self.results:
                txt = f"SSID: {result.get('ssid', 'N/A')} — {result.get('type', 'audit')} (success: {result.get('success', False)})"
                elements.append(Paragraph(txt, styles["Normal"]))
                elements.append(Spacer(1, 12))

            elements.append(Paragraph("Ethics &amp; Recommendations: Only audit networks you own or have explicit permission for.", styles["Normal"]))
            doc.build(elements)
            return os.path.abspath(output_path)
        except Exception:
            # Fallback to Markdown when PDF generation is unavailable
            md_path = output_path.replace(".pdf", ".md") if output_path.endswith(".pdf") else output_path + ".md"
            self.to_markdown(title, md_path)
            return md_path

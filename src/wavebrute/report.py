"""Report generation module for WaveBrute.

Uses ReportLab for PDF with neo-brutalist design (thick borders, screaming colors).
Uses Jinja2 for Markdown and HTML reports with matching brutalist CSS.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import jinja2
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


class ReportBuilder:
    """Builds professional audit reports in PDF, Markdown or HTML."""

    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    @classmethod
    def from_results(cls, results: list[dict[str, Any]]) -> ReportBuilder:
        """Create builder populated with audit results."""
        builder = cls()
        builder.results = list(results)
        return builder

    def to_pdf(
        self,
        title: str = "WaveBrute Ethical Audit Report",
        output_path: str | None = None,
    ) -> str:
        """Generate PDF report with neo-brutalist styling."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wavebrute_report_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        brutal_style = ParagraphStyle(
            "Brutalist",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=colors.HexColor("#ff004d"),
            borderWidth=4,
            borderColor=colors.HexColor("#00ff9f"),
            borderPadding=10,
            spaceAfter=20,
        )

        heading2 = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#00ff9f"),
            backColor=colors.HexColor("#111111"),
            borderWidth=3,
            borderColor=colors.yellow,
            spaceAfter=12,
        )

        normal = ParagraphStyle(
            "Normal",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
        )

        story = []

        story.append(Paragraph(f"<b>{title}</b>", brutal_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Audit Summary", heading2))
        story.append(Paragraph(f"Generated: {datetime.now().isoformat()}", normal))
        story.append(Paragraph(f"Total results: {len(self.results)}", normal))
        story.append(Spacer(1, 20))

        if self.results:
            data = [["Type", "SSID", "Success", "Details"]]
            for res in self.results[:10]:
                row = [
                    res.get("type", "unknown"),
                    res.get("ssid", "N/A"),
                    str(res.get("success", "N/A")),
                    str(res.get("password") or res.get("pin") or res.get("notes", ""))[:50],
                ]
                data.append(row)

            table = Table(data, colWidths=[80, 100, 60, 220])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff004d")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0f0f0")),
                        ("GRID", (0, 0), (-1, -1), 2, colors.HexColor("#00ff9f")),
                        ("BOX", (0, 0), (-1, -1), 4, colors.yellow),
                    ]
                )
            )
            story.append(table)

        story.append(Spacer(1, 30))
        story.append(Paragraph("Recommendations", heading2))
        story.append(
            Paragraph(
                "• Always obtain explicit written consent before live testing.<br/>"
                "• Use strong, unique passwords and disable WPS.<br/>"
                "• Prefer WPA3 over older standards.<br/>"
                "• Monitor for unauthorized access points.",
                normal,
            )
        )

        doc.build(story)
        return os.path.abspath(output_path)

    def to_markdown(
        self,
        title: str = "WaveBrute Ethical Audit Report",
        output_path: str | None = None,
    ) -> str:
        """Generate Markdown report using Jinja2 template."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wavebrute_report_{timestamp}.md"

        template_str = """# {{ title }}

**Generated**: {{ timestamp }}

## Summary
- Networks audited: {{ num_results }}
- Simulations run: {{ num_simulations }}
- Success rate: {{ success_rate }}%

## Findings

{% for result in results %}
### {{ result.type|title }} - {{ result.get('ssid', 'N/A') }}
- Success: **{{ result.get('success', 'N/A') }}**
{% if result.get('password') %} - Password: `{{ result.password }}`{% endif %}
{% if result.get('pin') %} - PIN: `{{ result.pin }}`{% endif %}
- Attempts: {{ result.get('attempts', 'N/A') }}
{% if result.get('notes') %}
> {{ result.notes }}
{% endif %}

{% endfor %}

## Recommendations
- Use the Ethics Guard before any live operations.
- Disable WPS on all devices.
- Upgrade to WPA3.
- Monitor with tools like WaveBrute regularly.

---
*Report generated by WaveBrute v0.1.0. For educational and authorized pentesting only.*
"""

        template = jinja2.Template(template_str)

        num_simulations = sum(1 for r in self.results if r.get("simulation", False))
        successes = sum(1 for r in self.results if r.get("success") is True)
        success_rate = round((successes / len(self.results) * 100), 1) if self.results else 0

        context = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(self.results),
            "num_simulations": num_simulations,
            "success_rate": success_rate,
            "results": self.results,
        }

        content = template.render(**context)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return os.path.abspath(output_path)

    def to_html(
        self,
        title: str = "WaveBrute Ethical Audit Report",
        output_path: str | None = None,
    ) -> str:
        """Generate HTML report with neo-brutalist inline CSS using Jinja2."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wavebrute_report_{timestamp}.html"

        css = """
        body { 
            background: #111111; 
            color: #00ff9f; 
            font-family: 'Courier New', monospace; 
            padding: 40px; 
            line-height: 1.6;
        }
        h1, h2 { 
            color: #ff004d; 
            border: 6px solid #ffff00; 
            padding: 20px; 
            background: #000; 
            display: inline-block;
        }
        .brutalist-box {
            border: 4px solid #ff00ff;
            background: #1a1a1a;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 8px 8px 0 #ffff00;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            border: 4px solid #00ff9f;
        }
        th, td {
            padding: 12px;
            border: 2px solid #ffff00;
            text-align: left;
        }
        th {
            background: #ff004d;
            color: white;
        }
        """

        template_str = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>{{ css }}</style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p><strong>Generated:</strong> {{ timestamp }}</p>
    
    <div class="brutalist-box">
        <h2>Audit Summary</h2>
        <p>Total results: {{ num_results }} | Simulations: {{ num_simulations }} | Success rate: {{ success_rate }}%</p>
    </div>
    
    <h2>Findings</h2>
    {% for result in results %}
    <div class="brutalist-box">
        <h3>{{ result.type|title }} on {{ result.get('ssid', 'N/A') }}</h3>
        <p><strong>Success:</strong> {{ result.get('success', False) }}</p>
        {% if result.get('password') %}<p><strong>Password:</strong> <code>{{ result.password }}</code></p>{% endif %}
        {% if result.get('pin') %}<p><strong>PIN:</strong> <code>{{ result.pin }}</code></p>{% endif %}
        <p><strong>Attempts:</strong> {{ result.get('attempts', 'N/A') }}</p>
        {% if result.get('notes') %}<p><em>{{ result.notes }}</em></p>{% endif %}
    </div>
    {% endfor %}
    
    <div class="brutalist-box">
        <h2>Responsible Use Recommendations</h2>
        <ul>
            <li>Complete the ethics checklist before any live scan or attack.</li>
            <li>WPS should be disabled on all routers.</li>
            <li>Use WPA3 whenever possible.</li>
            <li>Only test networks you own or have explicit permission for.</li>
        </ul>
    </div>
    
    <footer style="margin-top: 50px; color: #666; border-top: 3px solid #ffff00; padding-top: 20px;">
        Generated by WaveBrute • Educational &amp; Ethical Pentesting Toolkit
    </footer>
</body>
</html>
"""

        template = jinja2.Template(template_str)

        num_simulations = sum(1 for r in self.results if r.get("simulation", False))
        successes = sum(1 for r in self.results if r.get("success") is True)
        success_rate = round((successes / len(self.results) * 100) if self.results else 0, 1)

        context = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(self.results),
            "num_simulations": num_simulations,
            "success_rate": success_rate,
            "results": self.results,
            "css": css,
        }

        content = template.render(**context)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return os.path.abspath(output_path)

"""Report generation for WaveBrute.

Supports professional PDF (via ReportLab with neo-brutalist styling),
Markdown, and HTML outputs. All formats include findings, timelines,
AI hints, recommendations and responsible-use disclaimers. Jinja2 is
used for HTML templating; ReportLab handles PDF layout with thick
borders and signature colors (#ff004d, #00ff9f).
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import jinja2
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportBuilder:
    """Builds audit reports in PDF, Markdown or HTML.

    The class collects results from Auditor and renders them into different
    formats. PDF uses ReportLab with brutalist styling. Markdown and HTML
    use simple but loud templates that match the neo-brutalist aesthetic.
    """

    def __init__(self, results: List[Dict[str, Any]]) -> None:
        """Initialize with audit results.

        Args:
            results: List of result dicts from Auditor.

        Raises:
            ValueError: If results is not a list.
        """
        if not isinstance(results, list):
            raise ValueError("results must be a list of dicts")
        self.results = results

    @classmethod
    def from_results(cls, results: List[Dict[str, Any]]) -> "ReportBuilder":
        """Create ReportBuilder from a list of audit result dicts.

        Args:
            results: List of result dictionaries.

        Returns:
            Configured ReportBuilder instance.
        """
        return cls(results)

    def to_pdf(self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.pdf") -> None:
        """Generate a PDF report using ReportLab with neo-brutalist design.

        Thick borders simulated via table styles, magenta (#ff004d) and
        lime (#00ff9f) accents, black borders.

        Args:
            title: Report title.
            output_path: Path where PDF will be written.
        """
        if not isinstance(title, str) or not title.strip():
            title = "WaveBrute Ethical Audit Report"
        if not isinstance(output_path, str) or not output_path.strip():
            output_path = "wavebrute_report.pdf"

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=colors.HexColor("#ff004d"),
            spaceAfter=30,
            borderColor=colors.black,
            borderWidth=6,
            borderPadding=(15, 15, 15, 15),
        )

        heading_style = ParagraphStyle(
            "HeadingStyle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#00ff9f"),
            backColor=colors.HexColor("#000000"),
            spaceAfter=12,
            borderWidth=3,
            borderColor=colors.black,
            borderPadding=(5, 8, 5, 8),
        )

        story = [Paragraph(title, title_style), Spacer(1, 30)]

        summary = (
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Total results: {len(self.results)}<br/>"
            "Mode: SAFE SIMULATION (ethical training / authorized testing only)"
        )
        story.append(Paragraph(summary, styles["Normal"]))
        story.append(Spacer(1, 20))

        for idx, result in enumerate(self.results):
            story.append(
                Paragraph(
                    f"Result {idx+1}: {result.get('type', 'Audit Finding').upper()}",
                    heading_style,
                )
            )

            rows = []
            for key, value in result.items():
                if key in ("recommendations", "notes", "timestamp", "type", "ai_suggestions_used"):
                    continue
                if isinstance(value, bool):
                    value = "YES" if value else "NO"
                if isinstance(value, (list, dict)):
                    value = str(value)[:80] + "..."
                rows.append([key.replace("_", " ").title(), str(value)])

            if rows:
                t = Table(rows, colWidths=[140, 280])
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff004d")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0f0f0")),
                            ("GRID", (0, 0), (-1, -1), 3, colors.black),
                            ("BOX", (0, 0), (-1, -1), 6, colors.black),
                        ]
                    )
                )
                story.append(t)

            if result.get("recommendations"):
                story.append(Spacer(1, 12))
                story.append(Paragraph("Recommendations:", styles["Heading3"]))
                for rec in result["recommendations"]:
                    story.append(Paragraph(f"• {rec}", styles["Normal"]))

            if result.get("notes"):
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"Notes: {result.get('notes')}", styles["Italic"]))

            story.append(Spacer(1, 30))

        story.append(
            Paragraph(
                "WaveBrute • Ethical simulation only • Always obtain explicit consent before live audits",
                ParagraphStyle(
                    "Footer",
                    parent=styles["Normal"],
                    fontSize=9,
                    textColor=colors.gray,
                    spaceBefore=30,
                ),
            )
        )

        doc.build(story)

    def to_markdown(self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.md") -> None:
        """Generate a Markdown report.

        Clean, readable MD with code blocks for passwords and lists for
        recommendations. Matches the style used in README and CLI output.

        Args:
            title: Report title.
            output_path: Path where Markdown will be written.
        """
        if not isinstance(title, str) or not title.strip():
            title = "WaveBrute Ethical Audit Report"
        if not isinstance(output_path, str) or not output_path.strip():
            output_path = "wavebrute_report.md"

        content = f"""# {title}

**Generated:** {datetime.now().isoformat()}
**Format:** Markdown
**Mode:** SAFE SIMULATION (ethical training and authorized pentests only)

## Summary
- **Total results:** {len(self.results)}
- **Networks simulated:** {sum(1 for r in self.results if r.get('type') in ('scan', 'brute_force_simulation'))}
- **PMKID simulations:** {sum(1 for r in self.results if r.get('type') == 'pmkid_simulation')}

---

"""

        for i, result in enumerate(self.results, 1):
            res_type = result.get("type", "unknown").replace("_", " ").title()
            content += f"## {i}. {res_type}\n\n"

            if "ssid" in result and result["ssid"]:
                content += f"**Target SSID:** {result['ssid']}\n\n"

            if "success" in result:
                status = "✅ SUCCESS" if result["success"] else "❌ No crack in this simulation"
                content += f"**Outcome:** {status}\n\n"

            if result.get("password"):
                content += f"**Discovered Password:** `{result['password']}`\n\n"

            if "attempts" in result:
                content += f"**Attempts:** {result.get('attempts', 0)}\n"
                content += f"**Duration:** {result.get('duration_seconds', 0)}s\n"
                content += f"**Words/sec:** {result.get('words_per_second', 0)}\n\n"

            if result.get("ai_suggestions_used"):
                content += f"**AI Suggestions Used:** {result['ai_suggestions_used']}\n\n"

            if result.get("recommendations"):
                content += "### Recommendations\n\n"
                for rec in result["recommendations"]:
                    content += f"- {rec}\n"
                content += "\n"

            if result.get("notes"):
                content += f"**Notes:** {result['notes']}\n\n"

            if result.get("timestamp"):
                content += f"*Timestamp: {result['timestamp']}*\n\n"

            content += "---\n\n"

        content += """
## Ethics & Responsible Use

This report was generated by **WaveBrute**. All operations were performed
in safe simulation mode with zero risk to real networks.

**You MUST:**
1. Obtain explicit written permission before any live testing.
2. Delete all data after authorized engagements.
3. Follow local laws and responsible disclosure practices.

---

*Generated by WaveBrute v0.1.0 — Ethical WiFi auditing toolkit*
"""

        Path(output_path).write_text(content, encoding="utf-8")

    def to_html(self, title: str = "WaveBrute Ethical Audit Report", output_path: str = "report.html") -> None:
        """Generate an HTML report with neo-brutalist styling.

        Uses inline CSS with thick borders, screaming colors (#ff004d, #00ff9f,
        yellow background) to match the desktop/Android GUI aesthetic. Powered
        by Jinja2 templating.

        Args:
            title: Report title.
            output_path: Path where HTML will be written.
        """
        if not isinstance(title, str) or not title.strip():
            title = "WaveBrute Ethical Audit Report"
        if not isinstance(output_path, str) or not output_path.strip():
            output_path = "wavebrute_report.html"

        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
        body {
            font-family: 'Press Start 2P', monospace;
            background: #fffb00;
            color: #000;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }
        h1 {
            background: #ff004d;
            color: #fff;
            padding: 30px;
            border: 8px solid #000;
            text-align: center;
            box-shadow: 8px 8px 0 #000;
            margin-bottom: 40px;
        }
        .summary {
            background: #00ff9f;
            border: 6px solid #000;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 6px 6px 0 #000;
        }
        .result {
            background: #fff;
            border: 6px solid #000;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 8px 8px 0 #000;
        }
        .result h2 {
            background: #ff004d;
            color: white;
            padding: 10px 20px;
            border: 4px solid #000;
            display: inline-block;
            margin-top: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 3px solid #000;
            padding: 12px;
            text-align: left;
        }
        th {
            background: #ff004d;
            color: white;
        }
        ul {
            list-style: none;
        }
        ul li {
            margin: 8px 0;
            padding-left: 25px;
            position: relative;
        }
        ul li:before {
            content: "►";
            position: absolute;
            left: 0;
            color: #ff004d;
        }
        .footer {
            margin-top: 60px;
            padding-top: 20px;
            border-top: 6px solid #000;
            font-size: 0.7em;
            text-align: center;
            color: #333;
        }
        code {
            background: #000;
            color: #00ff9f;
            padding: 2px 6px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>

    <div class="summary">
        <h2>AUDIT SUMMARY</h2>
        <p><strong>Generated:</strong> {{ generated }}</p>
        <p><strong>Results:</strong> {{ num_results }}</p>
        <p><strong>Mode:</strong> SAFE SIMULATION</p>
    </div>

    {% for result in results %}
    <div class="result">
        <h2>RESULT {{ loop.index }} — {{ result.type|upper|replace("_", " ") if result.type else 'UNKNOWN' }}</h2>

        {% if result.ssid %}
        <p><strong>SSID:</strong> {{ result.ssid }}</p>
        {% endif %}

        {% if result.success is defined %}
        <p><strong>Success:</strong>
            {% if result.success %}✅ CRACKED IN SIM{% else %}❌ NO CRACK THIS RUN{% endif %}
        </p>
        {% endif %}

        {% if result.password %}
        <p><strong>Password:</strong> <code>{{ result.password }}</code></p>
        {% endif %}

        {% if result.attempts %}
        <p><strong>Attempts:</strong> {{ result.attempts }} |
           <strong>Duration:</strong> {{ result.duration_seconds }}s</p>
        {% endif %}

        {% if result.ai_suggestions_used %}
        <p><strong>AI Hints Used:</strong> {{ result.ai_suggestions_used }}</p>
        {% endif %}

        {% if result.recommendations %}
        <h3 style="color:#ff004d; border-bottom: 4px solid #000; padding-bottom: 5px;">RECOMMENDATIONS</h3>
        <ul>
            {% for rec in result.recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        {% if result.notes %}
        <p><strong>Notes:</strong> {{ result.notes }}</p>
        {% endif %}

        <small style="color:#666;">{{ result.timestamp or '' }}</small>
    </div>
    {% endfor %}

    <div class="footer">
        <p>WAVEBRUTE ETHICAL AUDIT TOOLKIT • ALL ACTIONS WERE SIMULATED</p>
        <p>Only use on networks you own or have explicit written authorization to test.</p>
        <p>Made with ❤️ for responsible security trainers and red teams</p>
    </div>
</body>
</html>
"""

        template = jinja2.Template(html_template)
        context = {
            "title": title,
            "generated": datetime.now().isoformat(),
            "num_results": len(self.results),
            "results": self.results,
        }
        html_content = template.render(**context)
        Path(output_path).write_text(html_content, encoding="utf-8")

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template (reserved for future external template support)."""
        env = jinja2.Environment(loader=jinja2.BaseLoader())
        return env.from_string("{{ placeholder }}").render()


if __name__ == "__main__":
    # Self-contained runnable demo of all three formats
    from wavebrute.auditor import Auditor
    auditor = Auditor(simulation_mode=True)
    auditor.scan()
    auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
    auditor.simulate_pmkid_attack("IoT-Devices")
    builder = ReportBuilder.from_results(auditor.get_results())
    builder.to_markdown("Demo Markdown Report", "demo_report.md")
    builder.to_html("Demo HTML Report", "demo_report.html")
    builder.to_pdf("Demo PDF Report", "demo_report.pdf")
    print("Reports generated: demo_report.md / .html / .pdf")
    print("Markdown and HTML export feature demo completed successfully.")

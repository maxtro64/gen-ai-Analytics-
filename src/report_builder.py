"""
Report Builder — Converts LLM markdown output into styled HTML / PDF reports.
"""

import re
import datetime
from typing import Dict, Any, Optional


def markdown_to_html(md_text: str) -> str:
    """
    Simple markdown-to-HTML converter for the report sections.
    Handles headings, bold, lists, and paragraphs.
    """
    lines = md_text.strip().split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Headings
        if stripped.startswith("#### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h4>{stripped[5:]}</h4>")
        elif stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")

        # Numbered list
        elif re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^\d+\.\s", "", stripped)
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            if not in_list:
                html_lines.append("<ol>")
                in_list = True
            html_lines.append(f"  <li>{content}</li>")

        # Bullet list
        elif stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"  <li>{content}</li>")

        # Empty line
        elif stripped == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")

        # Regular paragraph
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            html_lines.append(f"<p>{content}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


REPORT_CSS = """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 30px;
    background: #ffffff;
    color: #1a1a2e;
    line-height: 1.7;
}
.report-header {
    border-bottom: 3px solid #0f3460;
    padding-bottom: 20px;
    margin-bottom: 30px;
}
.report-header h1 {
    color: #0f3460;
    font-size: 28px;
    margin-bottom: 5px;
}
.report-header .meta {
    color: #666;
    font-size: 14px;
}
h2 {
    color: #0f3460;
    border-left: 4px solid #e94560;
    padding-left: 12px;
    margin-top: 35px;
    font-size: 20px;
}
h3 { color: #16213e; font-size: 17px; margin-top: 25px; }
p { margin: 10px 0; }
ul, ol { margin: 10px 0 10px 20px; }
li { margin: 6px 0; }
strong { color: #0f3460; }
.kpi-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin: 20px 0;
}
.kpi-card {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 18px 22px;
    min-width: 180px;
    flex: 1;
    border-left: 4px solid #0f3460;
}
.kpi-card .label { font-size: 12px; color: #666; text-transform: uppercase; }
.kpi-card .value { font-size: 24px; font-weight: 700; color: #0f3460; }
.kpi-card .change { font-size: 13px; margin-top: 4px; }
.kpi-card .change.positive { color: #27ae60; }
.kpi-card .change.negative { color: #e74c3c; }
.footer {
    margin-top: 50px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    font-size: 12px;
    color: #999;
    text-align: center;
}
"""


def build_kpi_cards_html(overall_summary: Dict[str, Any]) -> str:
    """Generates the KPI summary cards section at the top of the report."""
    if not overall_summary:
        return ""

    cards = []
    for metric, data in overall_summary.items():
        label = metric.replace("_", " ").title()
        value = data.get("latest_value", "N/A")
        pct = data.get("pct_change")

        # Format large numbers
        if isinstance(value, (int, float)) and value >= 10000:
            display_val = f"${value:,.0f}" if "revenue" in metric.lower() or "spend" in metric.lower() else f"{value:,.0f}"
        elif isinstance(value, (int, float)):
            display_val = f"{value:,.2f}"
        else:
            display_val = str(value)

        if pct is not None:
            direction = "positive" if pct >= 0 else "negative"
            arrow = "▲" if pct >= 0 else "▼"
            change_html = f'<div class="change {direction}">{arrow} {pct:+.1f}% MoM</div>'
        else:
            change_html = ""

        cards.append(f"""
        <div class="kpi-card">
            <div class="label">{label}</div>
            <div class="value">{display_val}</div>
            {change_html}
        </div>""")

    return f'<div class="kpi-cards">{"".join(cards)}</div>'


def generate_report_chart_png(df: Optional[Any] = None, schema: Optional[Dict[str, Any]] = None) -> Optional[bytes]:
    """Generates a high-resolution, branded corporate chart in PNG format."""
    if df is None or schema is None:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        import io

        period_col = schema.get("period_col")
        metric_cols = schema.get("metric_cols", [])
        if not period_col or not metric_cols:
            return None

        primary_metric = metric_cols[0]
        agg = df.groupby(period_col)[primary_metric].sum().reset_index()
        if len(agg) < 2:
            return None

        fig, ax = plt.subplots(figsize=(6.8, 2.8), dpi=200)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#fafbfc")

        x = [str(p) for p in agg[period_col]]
        y = agg[primary_metric]

        ax.plot(x, y, marker="o", color="#0f3460", linewidth=2.4, markersize=5.5)
        ax.fill_between(x, y, color="#0f3460", alpha=0.08)

        metric_label = primary_metric.replace("_", " ").title()
        ax.set_title(f"{metric_label} Performance Trend", fontsize=10.5, fontweight="bold", color="#0f3460", pad=9)
        ax.tick_params(axis="both", which="major", labelsize=7.5, colors="#333333")
        ax.grid(True, linestyle="--", alpha=0.35, color="#bbbbbb")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#cccccc")
        ax.spines["bottom"].set_color("#cccccc")

        if y.max() >= 10000:
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"${val*1e-3:.0f}K" if val < 1e6 else f"${val*1e-6:.1f}M"))

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None


def build_full_html_report(
    narrative_md: str,
    overall_summary: Dict[str, Any],
    title: str = "Business Performance Report",
    department: Optional[str] = None,
    chart_bytes: Optional[bytes] = None,
) -> str:
    """
    Assembles the complete HTML report:
      - Header with title and date
      - KPI summary cards
      - Embedded corporate chart (if provided)
      - Converted markdown narrative
      - Footer
    """
    import base64
    now = datetime.datetime.now().strftime("%B %d, %Y")
    subtitle = f" — {department} Focus" if department else ""

    kpi_cards = build_kpi_cards_html(overall_summary)
    narrative_html = markdown_to_html(narrative_md)

    chart_html = ""
    if chart_bytes:
        b64_img = base64.b64encode(chart_bytes).decode("utf-8")
        chart_html = f"""
        <div style="margin: 25px 0; text-align: center;">
            <img src="data:image/png;base64,{b64_img}" style="max-width: 100%; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(15,52,96,0.06);" alt="Performance Trend Chart" />
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}{subtitle}</title>
    <style>{REPORT_CSS}</style>
</head>
<body>
    <div class="report-header">
        <h1>{title}{subtitle}</h1>
        <div class="meta">Generated on {now} | GenAI Business Report Generator</div>
    </div>

    {kpi_cards}

    {chart_html}

    <div class="report-body">
        {narrative_html}
    </div>

    <div class="footer">
        This report was generated using AI-assisted analysis. All metrics are derived from
        uploaded data. Verify critical figures before making business decisions.
    </div>
</body>
</html>"""

    return html
def build_pdf_report(
    narrative_md: str,
    overall_summary: Dict[str, Any],
    title: str = "Business Performance Report",
    department: Optional[str] = None,
    chart_bytes: Optional[bytes] = None,
) -> bytes:
    """Generates a PDF report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50, leftMargin=50, rightMargin=50)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontSize=22,
        leading=28,
        textColor=HexColor("#0f3460"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        fontSize=10,
        textColor=HexColor("#666666"),
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        fontSize=14,
        leading=20,
        textColor=HexColor("#0f3460"),
        spaceBefore=18,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontSize=10,
        leading=15,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="BulletItem",
        fontSize=10,
        leading=15,
        leftIndent=20,
        spaceAfter=4,
    ))

    elements = []
    now = datetime.datetime.now().strftime("%B %d, %Y")
    subtitle = f" — {department} Focus" if department else ""

    # Title
    elements.append(Paragraph(f"{title}{subtitle}", styles["ReportTitle"]))
    elements.append(Paragraph(f"Generated on {now} | GenAI Business Report Generator", styles["ReportSubtitle"]))
    elements.append(Spacer(1, 10))

    # KPI Summary Table
    if overall_summary:
        table_data = [["Metric", "Latest Value", "Previous", "Change %"]]
        for metric, data in overall_summary.items():
            label = metric.replace("_", " ").title()
            latest = f"{data['latest_value']:,.2f}"
            prev = f"{data['previous_value']:,.2f}" if data.get("previous_value") is not None else "N/A"
            pct = f"{data['pct_change']:+.1f}%" if data.get("pct_change") is not None else "N/A"
            table_data.append([label, latest, prev, pct])

        t = Table(table_data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8f9ff"), HexColor("#ffffff")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 14))

    # Embedded Chart
    if chart_bytes:
        try:
            chart_img = Image(io.BytesIO(chart_bytes), width=6.2 * inch, height=2.5 * inch)
            elements.append(chart_img)
            elements.append(Spacer(1, 14))
        except Exception:
            pass

    # Narrative sections
    for line in narrative_md.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 6))
        elif stripped.startswith("## "):
            elements.append(Paragraph(stripped[3:], styles["SectionHead"]))
        elif stripped.startswith("# "):
            elements.append(Paragraph(stripped[2:], styles["SectionHead"]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:]
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            elements.append(Paragraph(f"• {text}", styles["BulletItem"]))
        elif re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s", "", stripped)
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            elements.append(Paragraph(f"‣ {text}", styles["BulletItem"]))
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", stripped)
            elements.append(Paragraph(text, styles["BodyText2"]))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "This report was generated using AI-assisted analysis. Verify critical figures before making business decisions.",
        ParagraphStyle(name="Footer", fontSize=8, textColor=HexColor("#999999"), alignment=1),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

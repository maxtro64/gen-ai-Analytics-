"""
Generate Sample Reports
=======================
Generates and exports sample executive business reports (PDF, HTML, MD)
for both Sales and Marketing datasets to satisfy Deliverable #5.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.kpi_engine import run_full_analysis
from src.prompts import build_executive_summary_prompt
from src.llm_generator import generate_report
from src.report_builder import build_full_html_report, build_pdf_report, generate_report_chart_png

load_dotenv()


def generate_samples():
    os.makedirs("output", exist_ok=True)
    api_key = os.getenv("GEMINI_API_KEY")

    datasets = [
        ("data/sample_kpi_sales.csv", "Q2 Enterprise Sales Performance Report", "sales"),
        ("data/sample_kpi_marketing.csv", "Digital Marketing & Acquisition Performance Report", "marketing"),
    ]

    for filepath, title, slug in datasets:
        print(f"Processing {filepath}...")
        df = pd.read_csv(filepath)
        analysis = run_full_analysis(df)
        chart_bytes = generate_report_chart_png(df, analysis["schema"])

        sys_p, usr_p = build_executive_summary_prompt(analysis, tone="strategic")
        narrative = generate_report(sys_p, usr_p, provider="gemini", api_key=api_key, model="gemini-3.5-flash")

        # Save Markdown
        md_path = f"output/{slug}_performance_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(narrative)
        print(f"  Saved {md_path}")

        # Save HTML
        html = build_full_html_report(narrative, analysis["overall_summary"], title=title, chart_bytes=chart_bytes)
        html_path = f"output/{slug}_performance_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Saved {html_path}")

        # Save PDF
        pdf_bytes = build_pdf_report(narrative, analysis["overall_summary"], title=title, chart_bytes=chart_bytes)
        pdf_path = f"output/{slug}_performance_report.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  Saved {pdf_path}")

    print("\nAll sample reports successfully generated in output/ directory!")


if __name__ == "__main__":
    generate_samples()

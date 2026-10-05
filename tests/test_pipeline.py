"""
Unit and Integration Test Suite
================================
Validates deterministic computation, prompt structuring, PDF/HTML generation,
and LLM synthesis logic.
"""

import unittest
import pandas as pd
import os
from dotenv import load_dotenv

from src.kpi_engine import (
    detect_schema,
    compute_overall_summary,
    compute_segment_performance,
    detect_anomalies,
    run_full_analysis,
)
from src.prompts import (
    build_executive_summary_prompt,
    build_focused_prompt,
    build_chat_system_prompt,
)
from src.report_builder import build_full_html_report, build_pdf_report
from src.llm_generator import generate_report, generate_chat_response

load_dotenv()


class TestKPIEngine(unittest.TestCase):

    def setUp(self):
        # Sample synthetic dataframe with 2 periods and 2 regions
        self.df = pd.DataFrame({
            "Period": ["2024-01", "2024-01", "2024-02", "2024-02"],
            "Region": ["North", "South", "North", "South"],
            "Revenue": [100.0, 200.0, 150.0, 180.0],
            "Cost": [50.0, 80.0, 60.0, 90.0],
        })

    def test_detect_schema(self):
        schema = detect_schema(self.df)
        self.assertEqual(schema["period_col"], "Period")
        self.assertIn("Region", schema["segment_cols"])
        self.assertIn("Revenue", schema["metric_cols"])
        self.assertIn("Cost", schema["metric_cols"])

    def test_deterministic_summary(self):
        schema = detect_schema(self.df)
        summary = compute_overall_summary(self.df, schema)

        # Revenue: Period 1 total = 300, Period 2 total = 330
        # Change = +30 (+10.0%)
        rev = summary["Revenue"]
        self.assertEqual(rev["latest_value"], 330.0)
        self.assertEqual(rev["previous_value"], 300.0)
        self.assertEqual(rev["abs_change"], 30.0)
        self.assertAlmostEqual(rev["pct_change"], 10.0, places=1)

    def test_segment_performance(self):
        schema = detect_schema(self.df)
        segments = compute_segment_performance(self.df, schema)
        self.assertEqual(len(segments), 2)

        north = next(s for s in segments if s["segment_value"] == "North")
        # North revenue: 100 -> 150 (+50.0%)
        self.assertEqual(north["metrics"]["Revenue"]["latest"], 150.0)
        self.assertEqual(north["metrics"]["Revenue"]["previous"], 100.0)
        self.assertEqual(north["metrics"]["Revenue"]["mom_change_pct"], 50.0)

    def test_anomalies_empty_for_normal_data(self):
        schema = detect_schema(self.df)
        anomalies = detect_anomalies(self.df, schema)
        # Less than 3 periods should safely produce no false positive anomalies
        self.assertEqual(len(anomalies), 0)


class TestReportBuilder(unittest.TestCase):

    def setUp(self):
        self.overall = {
            "Revenue": {
                "latest_value": 500000.0,
                "previous_value": 450000.0,
                "pct_change": 11.1,
            }
        }
        self.narrative = "## Executive Summary\nRevenue increased significantly by **11.1%**.\n- High momentum in sales."

    def test_html_builder(self):
        html = build_full_html_report(self.narrative, self.overall, title="Q2 Brief")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Q2 Brief", html)
        self.assertIn("Revenue", html)
        self.assertIn("$500,000", html)

    def test_pdf_builder(self):
        pdf_bytes = build_pdf_report(self.narrative, self.overall, title="Q2 Brief")
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 500)
        # Verify PDF header magic bytes
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_chart_generation_and_embedding(self):
        from src.report_builder import generate_report_chart_png
        df = pd.DataFrame({
            "Period": ["2024-01", "2024-02", "2024-03"],
            "Revenue": [100000, 120000, 150000],
        })
        schema = {"period_col": "Period", "metric_cols": ["Revenue"]}
        chart_png = generate_report_chart_png(df, schema)
        self.assertIsNotNone(chart_png)
        assert chart_png is not None
        self.assertTrue(len(chart_png) > 1000)

        # Test embedding in HTML & PDF
        html = build_full_html_report(self.narrative, self.overall, chart_bytes=chart_png)
        self.assertIn("data:image/png;base64", html)

        pdf = build_pdf_report(self.narrative, self.overall, chart_bytes=chart_png)
        self.assertTrue(pdf.startswith(b"%PDF"))


class TestEvaluator(unittest.TestCase):

    def setUp(self):
        self.analysis = {
            "overall_summary": {
                "Revenue": {"latest_value": 3360000.0, "pct_change": 9.8},
                "EBITDA": {"latest_value": 982200.0, "pct_change": 27.0},
            }
        }

    def test_evaluator_accuracy(self):
        from src.evaluator import evaluate_narrative_accuracy
        truthful_text = "Revenue reached $3.36M in June, an increase of 9.8% MoM, with EBITDA at $982.2K (up 27%)."
        res = evaluate_narrative_accuracy(truthful_text, self.analysis)
        self.assertEqual(res["accuracy_score"], 100.0)
        self.assertEqual(res["hallucination_rate"], 0.0)
        self.assertIn("PASSED", res["verdict"])


class TestPrompts(unittest.TestCase):

    def test_prompt_generation(self):
        analysis = {"mock": "data"}
        sys_p, usr_p = build_executive_summary_prompt(analysis, tone="strategic")
        self.assertIn("strategic", sys_p.lower())
        self.assertIn("CRITICAL RULES", sys_p)
        self.assertIn("mock", usr_p)

    def test_chat_prompt_generation(self):
        analysis = {"mock": "data"}
        narrative = "Sample report"
        chat_sys = build_chat_system_prompt(analysis, narrative)
        self.assertIn("VERIFIED PRE-COMPUTED KPI DATA", chat_sys)
        self.assertIn("Sample report", chat_sys)


class TestLiveLLMIntegration(unittest.TestCase):

    def test_gemini_report_generation(self):
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            self.skipTest("No GEMINI_API_KEY available in .env")

        analysis = {
            "schema": {"period_col": "Period", "metric_cols": ["Sales"]},
            "overall_summary": {
                "Sales": {"latest_value": 1000, "previous_value": 800, "pct_change": 25.0}
            }
        }
        sys_p, usr_p = build_executive_summary_prompt(analysis, tone="concise")
        report = generate_report(sys_p, usr_p, provider="gemini", api_key=key, model="gemini-3.5-flash")
        self.assertTrue(len(report) > 50)

    def test_gemini_chat_assistant(self):
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            self.skipTest("No GEMINI_API_KEY available in .env")

        analysis = {
            "overall_summary": {
                "Revenue": {"latest_value": 120000, "pct_change": 15.0}
            }
        }
        chat_sys = build_chat_system_prompt(analysis, "Revenue grew 15%.")
        messages = [{"role": "user", "content": "What was the revenue growth percentage?"}]
        reply = generate_chat_response(messages, chat_sys, provider="gemini", api_key=key, model="gemini-3.5-flash")
        self.assertIn("15", reply)


if __name__ == "__main__":
    unittest.main()

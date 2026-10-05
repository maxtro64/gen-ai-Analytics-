"""
Prompt Templates — Structured Prompts for Executive Report Generation
=====================================================================
Each template has dynamic slots filled with pre-computed KPI data.
The LLM only handles narrative synthesis — never math.
"""

import json
from typing import Dict, Any, Tuple


TONE_INSTRUCTIONS = {
    "formal": (
        "Use a formal, corporate tone suitable for a board-level audience. "
        "Write in third person. Avoid contractions and colloquialisms."
    ),
    "strategic": (
        "Use a strategic advisory tone, similar to a McKinsey or BCG consultant briefing. "
        "Focus on implications, trade-offs, and prioritized actions."
    ),
    "concise": (
        "Be extremely concise. Use short sentences and bullet points. "
        "Every sentence must deliver a specific insight or action item. No filler."
    ),
}


SYSTEM_PROMPT = """You are a senior business analyst at a top-tier consulting firm.
Your job is to write executive business reports from pre-computed KPI data.

CRITICAL RULES — VIOLATION OF ANY RULE IS UNACCEPTABLE:
1. ONLY use the numbers and facts provided in the data below. NEVER invent, estimate, or hallucinate any metric, percentage, or cause.
2. If a cause or reason is not evident from the data, say "further investigation is needed" — do NOT speculate.
3. NEVER use technical / ML jargon (p-values, regression, loss, MSE, variance, standard deviation, z-score). Write for executives.
4. Every number you mention must exactly match the data provided. Do not round differently or paraphrase a number.
5. Structure the report in clean markdown with the sections requested.
6. {tone_instruction}
"""


def build_executive_summary_prompt(analysis: Dict[str, Any], tone: str = "formal") -> Tuple[str, str]:
    """
    Builds the system + user prompt pair for a comprehensive, consulting-grade executive report.
    Returns (system_prompt, user_prompt).
    """
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["formal"])
    system = SYSTEM_PROMPT.format(tone_instruction=tone_instruction)

    data_block = json.dumps(analysis, indent=2, default=str)

    user_prompt = f"""Below is the complete pre-computed KPI analysis for this reporting period.
All numbers are verified and final — use them exactly as provided.

=== PRE-COMPUTED KPI DATA ===
{data_block}
=== END DATA ===

Write a thorough, consulting-grade executive business report in clean markdown using the following structure:

## 1. Executive Snapshot & Core Takeaways
- **Top 3 Headline Takeaways**: Provide 3 high-impact bullet points summarizing the most critical results (bold key metrics: revenue, growth %, margin changes).
- **Macro Performance Summary**: 2 detailed paragraphs explaining the overarching state of the business, key momentum drivers, and forward-looking guidance.

## 2. KPI Financial & Operational Deep-Dive
- For every primary metric in the dataset, provide an in-depth analysis citing:
  * Latest Period Value vs Previous Period Value
  * Absolute Change and Month-over-Month (MoM) Percentage Variance
  * Margin or unit economics implications (e.g. EBITDA margin expansion, CAC vs ROAS efficiency, conversion momentum).

## 3. Segment & Channel Dynamics (Winners vs. Laggards)
- **Top Performer vs. Bottom Performer**: Identify the #1 leading segment and the trailing segment. Detail the specific performance gap between them.
- **Granular Segment Breakdown**: For each segment (region, channel, or product line), detail what improved, what deteriorated, and the primary operational drivers suggested by the metrics.

## 4. Operational Health & Statistical Outliers
- If any statistical anomalies or outliers were detected, evaluate each one:
  * Cite the exact period, metric, value, and deviation from historical baseline mean.
  * Provide a data-grounded business hypothesis for why this spike or dip occurred.
- If no anomalies were detected, summarize the operational stability and baseline consistency across periods.

## 5. Strategic Risk Register & Vulnerabilities
- Detail 3 distinct business risks emerging from negative trends, rising costs, margin contraction, or slowing volume in the data.
- For each risk, state:
  * **Risk Title & Severity** (High / Medium / Low)
  * **Observed Data Signal**: The specific metrics indicating this risk.
  * **Potential Business Impact**: Potential consequence if left unaddressed.
  * **Recommended Containment**: Concrete mitigation strategy.

## 6. High-Impact Value Creation Opportunities
- Detail 3 immediate, high-ROI opportunities to accelerate growth or optimize costs based on positive momentum signals in the data.
- Explain where leadership should allocate capital, marketing budget, or sales focus for maximum return.

## 7. Prioritized 30-60-90 Day Execution Roadmap
Provide a concrete execution roadmap with cross-functional ownership:
- **Immediate (Days 1–30)**: 2 quick-win interventions to address emerging bottlenecks. (Specify Owner: e.g., *VP of Sales* or *Head of Growth*).
- **Medium-Term (Days 31–60)**: 2 operational adjustments or resource reallocations. (Specify Owner).
- **Strategic (Days 61–90)**: 1-2 structural or platform enhancements to cement long-term gains. (Specify Owner).

CRITICAL INSTRUCTIONS:
- Quote all numbers with exact fidelity from the data payload. Do NOT round differently or fabricate figures.
- Use professional executive consulting vocabulary (McKinsey/BCG style).
- No machine learning or technical statistical jargon (no 'z-score', 'p-value', 'regression').
"""
    return system, user_prompt


def build_focused_prompt(
    analysis: Dict[str, Any],
    department: str,
    tone: str = "formal",
) -> Tuple[str, str]:
    """
    Builds a deep department-focused prompt (Sales, Marketing, or Operations).
    Returns (system_prompt, user_prompt).
    """
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["formal"])
    system = SYSTEM_PROMPT.format(tone_instruction=tone_instruction)

    data_block = json.dumps(analysis, indent=2, default=str)

    user_prompt = f"""Below is the complete pre-computed KPI analysis.
All numbers are verified — use them exactly as provided.

=== PRE-COMPUTED KPI DATA ===
{data_block}
=== END DATA ===

Write a comprehensive, deep-dive {department} Performance Report in markdown with these sections:

## 1. {department} Executive Summary & Core Takeaways
- 3 high-impact bullet points summarizing the department's top wins, challenges, and headline numbers.
- 2 paragraphs synthesizing overall departmental health, efficiency, and period-over-period trajectory.

## 2. Departmental KPI Deep-Dive & Variance Analysis
- Detailed walkthrough of every metric relevant to {department}, citing latest value, previous value, and exact MoM % changes.
- In-depth efficiency analysis (e.g. CAC/ROAS if Marketing, Revenue/Quota if Sales, Cycle Time/Volume if Operations).

## 3. Segment & Operational Breakdown
- Performance across channels, regions, or categories within the {department} portfolio.
- Identify the highest performing cohort and the lowest performing cohort with gap analysis.

## 4. Departmental Risks & Operational Bottlenecks
- 3 prioritized operational risks visible in the metrics, with severity, business impact, and mitigation steps.

## 5. Departmental Growth & Efficiency Levers
- 3 high-impact opportunities to improve productivity, reduce cost per unit, or accelerate pipeline.

## 6. {department} Leadership Action Plan (30-60-90 Day Roadmap)
- Concrete 30, 60, and 90-day action items with specific functional owners and success milestones.

REMINDER: Only reference verified numbers from the data above. Do not invent any figures.
"""
    return system, user_prompt


def build_chat_system_prompt(analysis: Dict[str, Any], narrative: str = "") -> str:
    """
    Builds the system prompt for the conversational AI assistant.
    Provides verified KPI data and the generated report as ground truth.
    """
    data_block = json.dumps(analysis, indent=2, default=str)
    report_context = f"\n=== GENERATED EXECUTIVE REPORT ===\n{narrative}\n=== END REPORT ===\n" if narrative else ""

    return f"""You are an executive business analyst and conversational advisor.
You are helping business executives, managers, and analysts understand their KPI data and report.

=== VERIFIED PRE-COMPUTED KPI DATA ===
{data_block}
=== END DATA ===
{report_context}
CRITICAL RULES:
1. ONLY cite verified facts and numbers from the pre-computed data and report above. NEVER invent or hallucinate metrics.
2. If asked about a cause not clear from the data, note that the data indicates the trend, but operational root cause requires deeper investigation.
3. Be clear, strategic, and concise. Format responses with clean markdown (bullet points, bold text).
4. If asked to draft communications (emails, memo bullets, executive summaries), tailor them professionally for C-suite and leadership.
5. Do not use obscure ML jargon. Speak in terms of business impact, revenue, margin, costs, and strategic actions.
"""

"""
GenAI Business Report Generator — Streamlit Application
========================================================
Upload CSV/Excel KPI data → Deterministic analysis → LLM narrative → HTML/PDF export → Interactive Conversational Q&A
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv

from src.kpi_engine import run_full_analysis, detect_schema
from src.prompts import build_executive_summary_prompt, build_focused_prompt, build_chat_system_prompt
from src.llm_generator import generate_report, generate_chat_response
from src.report_builder import build_full_html_report, build_pdf_report, generate_report_chart_png
from src.evaluator import evaluate_narrative_accuracy

load_dotenv()

def clean_markdown_for_display(text: str) -> str:
    r"""Escapes currency dollar signs (e.g. $3.36M -> \$3.36M) so Streamlit doesn't parse them as LaTeX."""
    import re
    if not text:
        return ""
    return re.sub(r"\$(?=\d)", r"\$", text)

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GenAI Business Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f3460;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
        margin-bottom: 25px;
    }
    .kpi-box {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .kpi-box h3 { color: #a8d8ea; font-size: 13px; margin: 0; text-transform: uppercase; }
    .kpi-box h1 { color: white; font-size: 28px; margin: 8px 0 4px 0; }
    .kpi-box p { font-size: 13px; margin: 0; }
    .positive { color: #2ecc71; }
    .negative { color: #e74c3c; }
    .stDownloadButton > button {
        background: #0f3460;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
    }
    .quick-prompt-btn {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">📊 GenAI Business Report Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload your KPI data → Get an executive-ready narrative report & conversational AI assistant</p>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("LLM Provider")
    default_provider = os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else "nvidia")
    provider_options = ["gemini", "nvidia", "openai"]
    default_idx = provider_options.index(default_provider) if default_provider in provider_options else 0

    provider: str = str(st.selectbox("Provider", provider_options, index=default_idx) or "gemini")

    env_key = os.getenv(f"{provider.upper()}_API_KEY", "")
    api_key = st.text_input(
        f"API Key ({provider.upper()})",
        value=env_key,
        type="password",
        placeholder="Enter API key or set in .env",
    )

    if provider == "openai":
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano"], index=0)
    elif provider == "nvidia":
        model = st.text_input(
            "Model Name (Copy from build.nvidia.com)", 
            value=os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
        )
    else:
        model = st.selectbox(
            "Model", 
            ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-pro-preview"], 
            index=0
        )

    st.divider()
    st.subheader("Report Settings")
    tone: str = str(st.selectbox("Tone", ["formal", "strategic", "concise"], index=0) or "formal")
    department: str = str(st.selectbox("Department Focus", ["General (All)", "Sales", "Marketing", "Operations"], index=0) or "General (All)")
    report_title: str = str(st.text_input("Report Title", value="Business Performance Report") or "Business Performance Report")

    st.divider()
    st.caption("All math is computed deterministically in Python. The LLM only generates the narrative text and answers questions.")

# ── File Upload ──────────────────────────────────────────────────────────────
st.subheader("📁 Upload KPI Data")
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file with your KPI metrics",
    type=["csv", "xlsx", "xls"],
    help="File should have a period/date column, optional segment columns, and numeric metric columns.",
)


# ── Main Logic ───────────────────────────────────────────────────────────────
if uploaded_file is not None:
    # Load data
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    st.success(f"✅ Loaded **{uploaded_file.name}** — {len(df)} rows × {len(df.columns)} columns")

    # Show raw data preview
    with st.expander("📋 Raw Data Preview", expanded=False):
        st.dataframe(df, use_container_width=True)

    # ── Step 1: Deterministic KPI Analysis ───────────────────────────────
    st.subheader("🔢 KPI Analysis (Deterministic)")

    with st.spinner("Computing KPI metrics..."):
        analysis = run_full_analysis(df)
        st.session_state["analysis"] = analysis

    schema = analysis["schema"]
    overall = analysis["overall_summary"]

    # Display KPI cards
    if overall:
        cols = st.columns(min(len(overall), 4))
        for i, (metric, data) in enumerate(overall.items()):
            with cols[i % len(cols)]:
                value = data["latest_value"]
                pct = data.get("pct_change")

                # Format display
                if isinstance(value, (int, float)) and value >= 10000:
                    display_val = f"${value:,.0f}" if any(k in metric.lower() for k in ["revenue", "spend", "sales"]) else f"{value:,.0f}"
                else:
                    display_val = f"{value:,.2f}"

                if pct is not None:
                    arrow = "▲" if pct >= 0 else "▼"
                    color_class = "positive" if pct >= 0 else "negative"
                    change_text = f'<p class="{color_class}">{arrow} {pct:+.1f}% MoM</p>'
                else:
                    change_text = ""

                label = metric.replace("_", " ").title()
                st.markdown(f"""
                <div class="kpi-box">
                    <h3>{label}</h3>
                    <h1>{display_val}</h1>
                    {change_text}
                </div>
                """, unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────
    st.subheader("📈 Visual Trends")

    period_col = schema.get("period_col")
    metric_cols = schema.get("metric_cols", [])
    segment_cols = schema.get("segment_cols", [])

    if period_col and metric_cols:
        chart_metric: str = str(st.selectbox("Select metric to visualize", metric_cols, index=0) or metric_cols[0])

        col1, col2 = st.columns(2)

        with col1:
            if segment_cols:
                fig = px.line(
                    df, x=period_col, y=chart_metric, color=segment_cols[0],
                    title=f"{chart_metric.replace('_', ' ').title()} Over Time",
                    markers=True,
                )
            else:
                agg = df.groupby(period_col)[chart_metric].sum().reset_index()
                fig = px.line(
                    agg, x=period_col, y=chart_metric,
                    title=f"{chart_metric.replace('_', ' ').title()} Over Time",
                    markers=True,
                )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if segment_cols:
                latest = df[df[period_col] == df[period_col].max()]
                fig2 = px.bar(
                    latest, x=segment_cols[0], y=chart_metric,
                    title=f"{chart_metric.replace('_', ' ').title()} by {segment_cols[0].replace('_', ' ').title()} (Latest Period)",
                    color=segment_cols[0],
                )
                fig2.update_layout(template="plotly_white", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No segment column detected for bar chart.")

    # Show anomalies with advanced statistical indicators
    if analysis.get("anomalies"):
        with st.expander("⚠️ Detected Statistical Anomalies & Outliers", expanded=True):
            for a in analysis["anomalies"]:
                direction_emoji = "🔺" if a["direction"] == "spike" else "🔻"
                severity = a.get("severity", "Moderate")
                iqr_tag = " (IQR Outlier)" if a.get("is_iqr_outlier") else ""
                st.warning(
                    f"**[{severity.upper()}]** {direction_emoji} **{a['metric']}** in **{a['period']}**: "
                    f"value = {a['value']:,.2f} (Z: {a['z_score']}, {a.get('deviation_pct_from_mean', 0):+.1f}% vs baseline mean){iqr_tag}"
                )

    # ── Step 2: Generate Narrative ───────────────────────────────────────
    st.divider()
    st.subheader("✍️ Generate Executive Report")

    effective_key = api_key or os.getenv(f"{provider.upper()}_API_KEY", "")
    if not effective_key:
        st.warning(f"⬅️ Enter your {provider.upper()} API key in the sidebar to generate the report.")

    generate_btn = st.button("🚀 Generate Report", type="primary", disabled=not effective_key)

    if generate_btn and effective_key:
        with st.spinner("Generating executive narrative with AI..."):
            try:
                dept = None if department == "General (All)" else department
                if dept:
                    system_prompt, user_prompt = build_focused_prompt(analysis, dept, tone)
                else:
                    system_prompt, user_prompt = build_executive_summary_prompt(analysis, tone)

                narrative = generate_report(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    provider=provider,
                    api_key=effective_key,
                    model=model,
                )

                st.session_state["narrative"] = narrative
                st.session_state["department"] = dept
                st.session_state["report_title"] = report_title

            except Exception as e:
                st.error(f"❌ LLM generation failed: {e}")

    # ── Step 3: Display & Export ─────────────────────────────────────────
    if "narrative" in st.session_state:
        narrative = st.session_state["narrative"]

        st.subheader("📄 Generated Report")
        st.markdown(clean_markdown_for_display(narrative))

        # Generate chart bytes for embedding in HTML & PDF
        chart_bytes = generate_report_chart_png(df, schema)

        # ── Automated LLM Evaluation & Hallucination Guardrail Check ──────
        eval_results = evaluate_narrative_accuracy(narrative, analysis)
        st.markdown("#### 🛡️ Automated LLM Factuality & Grounding Evaluation")
        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
            st.metric("Factuality Score", f"{eval_results['accuracy_score']}%", "Zero Hallucination" if eval_results['accuracy_score'] >= 95 else "Review Claims")
        with ev_col2:
            st.metric("Audited Numeric Claims", f"{eval_results['verified_claims']} / {eval_results['total_claims']} Verified")
        with ev_col3:
            st.metric("Hallucination Rate", f"{eval_results['hallucination_rate']}%")

        with st.expander("🔍 View Automated Grounding Audit Trail", expanded=False):
            st.write(f"**Audit Verdict:** {eval_results['verdict']}")
            if eval_results["audit_log"]:
                st.dataframe(pd.DataFrame(eval_results["audit_log"]), use_container_width=True)

        # Build HTML with embedded chart
        html_report = build_full_html_report(
            narrative_md=narrative,
            overall_summary=analysis.get("overall_summary", {}),
            title=st.session_state.get("report_title", "Business Performance Report"),
            department=st.session_state.get("department"),
            chart_bytes=chart_bytes,
        )

        st.divider()
        col_dl1, col_dl2, col_dl3 = st.columns(3)

        with col_dl1:
            st.download_button(
                label="📥 Download HTML Report",
                data=html_report,
                file_name="business_report.html",
                mime="text/html",
            )

        with col_dl2:
            st.download_button(
                label="📥 Download Narrative (Markdown)",
                data=narrative,
                file_name="business_report.md",
                mime="text/markdown",
            )

        with col_dl3:
            pdf_bytes = build_pdf_report(
                narrative_md=narrative,
                overall_summary=analysis.get("overall_summary", {}),
                title=st.session_state.get("report_title", "Business Performance Report"),
                department=st.session_state.get("department"),
                chart_bytes=chart_bytes,
            )
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name="business_report.pdf",
                mime="application/pdf",
            )

    # ── Step 4: Conversational AI Assistant (Chat with Your Data) ────────
    st.divider()
    st.subheader("💬 AI Business Assistant — Conversational Q&A")
    st.caption("Ask questions, explore specific segments, or request tailored email briefings from your data.")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI Business Analyst. Ask me anything about your KPI data, trends, segment comparisons, or request an executive briefing email.",
            }
        ]

    # Quick prompt buttons
    st.markdown("**Suggested Questions:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    prompt_to_send = None

    with q_col1:
        if st.button("🔍 Top risks for executive leadership?", use_container_width=True):
            prompt_to_send = "What are the top 3 risks in this dataset that I should present to executive leadership?"
    with q_col2:
        if st.button("✉️ Draft 3-bullet CEO email update", use_container_width=True):
            prompt_to_send = "Draft a 3-bullet concise email update for the CEO summarizing our latest performance and immediate next steps."
    with q_col3:
        if st.button("🏆 Compare best vs worst performers", use_container_width=True):
            prompt_to_send = "Compare our highest performing and lowest performing segments in detail. What explains the gap?"

    # Display chat conversation
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(clean_markdown_for_display(msg["content"]))

    # Chat input
    user_query = st.chat_input("Ask any question about your KPI data or report...")
    actual_query = prompt_to_send or user_query

    if actual_query:
        if not effective_key:
            st.warning("Please provide an API key in the sidebar to chat with the assistant.")
        else:
            # Append user message
            st.session_state["chat_messages"].append({"role": "user", "content": actual_query})
            with st.chat_message("user"):
                st.markdown(actual_query)

            # Generate reply
            with st.chat_message("assistant"):
                with st.spinner("Analyzing data and generating answer..."):
                    try:
                        current_narrative = st.session_state.get("narrative", "")
                        chat_sys = build_chat_system_prompt(analysis, current_narrative)

                        # Exclude initial welcome greeting from API call
                        history_for_api = [
                            m for m in st.session_state["chat_messages"]
                            if m.get("content") != "Hello! I am your AI Business Analyst. Ask me anything about your KPI data, trends, segment comparisons, or request an executive briefing email."
                        ]

                        reply = generate_chat_response(
                            messages=history_for_api,
                            system_prompt=chat_sys,
                            provider=provider,
                            api_key=effective_key,
                            model=model,
                        )
                        st.markdown(clean_markdown_for_display(reply))
                        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

                    except Exception as e:
                        err_msg = f"❌ Assistant error: {e}"
                        st.error(err_msg)

else:
    # Landing state
    st.info("👆 Upload a CSV or Excel file to get started. Sample files are in the `data/` folder.")

    with st.expander("💡 What kind of data works best?"):
        st.markdown("""
        Your file should have:
        - **A time/period column** (e.g., `Period`, `Month`, `Date`)
        - **Segment columns** (e.g., `Region`, `Channel`, `Warehouse`) — optional
        - **Numeric KPI columns** (e.g., `Revenue`, `CAC`, `Conversion_Rate_Pct`, `Churn_Rate_Pct`)

        **Example columns:** `Period, Region, Product_Line, Revenue, Target_Revenue, Gross_Margin_Pct, New_Customers`
        """)

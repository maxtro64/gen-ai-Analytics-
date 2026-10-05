# GenAI-Based Business Report Generator

An enterprise-grade Generative AI application that transforms raw KPI datasets (CSV/Excel) into consulting-grade executive narratives, polished HTML/PDF business reports, and interactive conversational analysis.

---

## 1. Problem Statement
Executives and senior leaders do not want raw dashboards or dense spreadsheets. Dashboards communicate numbers, but leadership requires:
* **Context & Causality:** *What happened and why did it happen?*
* **Risks & Opportunities:** Highlighting threats before they escalate and capturing positive momentum.
* **Prioritized Actions:** Specific, data-backed next steps aligned with corporate objectives.

Traditional reporting requires business analysts to manually extract numbers, write summary slides, and draft emails—a process prone to delays, inconsistent narratives, and human error. This solution implements a **Deterministic Compute + Generative Narrative** architecture that automates end-to-end report generation while enforcing strict mathematical truthfulness.

---

## 2. Architecture & Data Preprocessing Logic

```
┌─────────────────────────────────┐
│     Structured KPI Data         │
│     (CSV / Excel Upload)        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    Deterministic KPI Engine     │  <-- 100% Python / Pandas / NumPy
│  • Automated Schema Detection   │      (Zero LLM Math)
│  • MoM Variance & % Changes     │
│  • Segment Performance Ranking  │
│  • Statistical Anomaly (Z-score)│
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Structured Prompt Builder     │  <-- Ground Truth Injection
│  • Injects verified JSON metrics│      (Anti-Hallucination Guardrails)
│  • Tone Customization           │
│  • Department Focus Routing     │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       LLM Synthesis Layer       │  <-- Gemini / NVIDIA NIM / OpenAI
│  • Executive Narrative Summary  │      (Automatic Model Failover)
│  • Performance Drivers & Trends │
│  • Strategic Recommendations    │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌───────────────┐ ┌───────────────┐
│  Polished     │ │ Conversational│
│  HTML & PDF   │ │ AI Assistant  │
│  Reports      │ │ (Data Q&A)    │
└───────────────┘ └───────────────┘
```

### Deterministic Preprocessing (`src/kpi_engine.py`)
1. **Automated Schema Detection:** Columns are classified dynamically into:
   - `period`: Time-axis column (`Period`, `Date`, `Month`).
   - `segment`: Categorical grouping (`Region`, `Channel`, `Product`).
   - `metric`: Numerical measurements (`Revenue`, `CAC`, `ROAS`, `EBITDA`).
2. **Month-over-Month (MoM) Analytics:** Computes absolute change and percentage change across adjacent reporting periods.
3. **Segment Ranking:** Sorts and assigns rankings across segments to identify top and bottom performers.
4. **Statistical Outlier Detection:** Implements a Z-score threshold ($|Z| \ge 1.5$) across historical aggregates to flag operational anomalies.

---

## 3. Prompt Design & Templates (`src/prompts.py`)

### Design Philosophy
* **Zero Math in the LLM:** The LLM is never asked to add, subtract, calculate percentages, or compute averages. All metrics are passed as pre-computed, final values.
* **Strict Anti-Hallucination Guardrails:** The system prompt enforces 6 inviolable rules:
  1. Only reference verified numbers present in the injected payload.
  2. If an underlying cause is not in the data, state that further investigation is required rather than speculating.
  3. Prohibit technical/ML jargon (e.g., loss, p-value, standard deviation) in favor of executive terminology.
  4. Ensure numerical consistency across all sections.
  5. Structure outputs using clear markdown headings and bullet points.
  6. Adapt tone based on persona (Formal, Strategic, or Concise).

---

## 4. Multi-Format Report Builder (`src/report_builder.py`)
* **HTML Reports:** Responsive, standalone HTML files styled with modern typography, KPI summary cards, color-coded delta indicators (▲ positive, ▼ negative), and executive branding.
* **PDF Reports:** Generated deterministically via ReportLab using corporate document templates, structured tables, and clean layout hierarchy.
* **Markdown:** Exportable raw markdown for direct integration into emails, Notion, or internal wikis.

---

## 5. Conversational AI Assistant
An interactive Q&A assistant embedded in the Streamlit application allowing executives and analysts to:
* Drill down into specific segments (*"Why did CAC spike in Paid Social?"*).
* Compare channels (*"Compare Google Search Ads vs LinkedIn B2B"*).
* Generate tailored briefings (*"Draft a 3-bullet email update for the CEO"*).
* All conversation turns maintain grounded context over the pre-computed metrics and generated report.

---

## 6. Project Structure

```
genai_project/
├── app.py                      # Streamlit interactive application
├── src/
│   ├── kpi_engine.py           # Deterministic data processing & anomaly detection
│   ├── prompts.py              # Structured prompt templates & chat system prompts
│   ├── llm_generator.py        # LLM client with multi-provider failover
│   └── report_builder.py       # HTML and PDF document generators
├── data/
│   ├── sample_kpi_sales.csv     # Sample regional sales & EBITDA dataset
│   └── sample_kpi_marketing.csv # Sample multi-channel digital acquisition dataset
├── output/
│   ├── sales_performance_report.html
│   ├── sales_performance_report.pdf
│   ├── sales_performance_report.md
│   ├── marketing_performance_report.html
│   ├── marketing_performance_report.pdf
│   └── marketing_performance_report.md
├── scripts/
│   ├── create_sample_data.py   # Dataset generator
│   └── generate_sample_reports.py # Batch report exporter
├── tests/
│   └── test_pipeline.py        # Comprehensive unit & integration test suite
├── .env.example                # Environment variables template
└── requirements.txt            # Python dependencies
```

---

## 7. How to Run

### 1. Setup Environment
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional alternatives:
OPENAI_API_KEY=your_openai_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Test Suite
```bash
python -m unittest tests/test_pipeline.py -v
```

---

## 8. Limitations & Future Extensions
* **Time-Series Horizon:** Currently optimized for Month-over-Month (MoM) and Quarter-over-Quarter comparisons. Extending to multi-year seasonality models would further enhance trend analysis.
* **External Factor Correlation:** Macro-economic indicators (inflation, competitor actions) are not captured in internal CSVs and must be supplemented by external research tools.
#   g e n - a i - A n a l y t i c s -  
 
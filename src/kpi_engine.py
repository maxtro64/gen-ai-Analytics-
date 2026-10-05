"""
KPI Engine — Deterministic Data Analysis Layer
===============================================
All numerical computations happen HERE, never inside the LLM.
The LLM receives only pre-computed, verified numbers.
"""

import pandas as pd
from typing import Dict, Any, List, Optional


def detect_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspects an uploaded DataFrame and classifies each column as:
      - 'period'      : date/time column used as the time axis
      - 'segment'     : categorical column (region, channel, warehouse, etc.)
      - 'metric'      : numeric KPI column
    """
    period_col = None
    segment_cols = []
    metric_cols = []

    for col in df.columns:
        col_lower = col.lower().strip()

        if col_lower in ("period", "month", "date", "year", "quarter", "week", "time"):
            period_col = col
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            metric_cols.append(col)
        else:
            try:
                pd.to_datetime(df[col], format="mixed")
                if period_col is None:
                    period_col = col
                else:
                    segment_cols.append(col)
            except (ValueError, TypeError):
                segment_cols.append(col)

    return {
        "period_col": period_col,
        "segment_cols": segment_cols,
        "metric_cols": metric_cols,
        "row_count": len(df),
    }


def compute_overall_summary(df: pd.DataFrame, schema: Dict) -> Dict[str, Any]:
    period_col = schema["period_col"]
    metric_cols = schema["metric_cols"]

    if period_col is None or not metric_cols:
        return {}

    df_sorted = df.sort_values(period_col)
    periods = df_sorted[period_col].unique()
    summary = {}

    for metric in metric_cols:
        agg = df_sorted.groupby(period_col)[metric].sum().sort_index()

        if len(agg) < 2:
            latest = agg.iloc[-1]
            summary[metric] = {
                "latest_period": str(periods[-1]),
                "latest_value": round(float(latest), 2),
                "previous_value": None, "abs_change": None, "pct_change": None,
                "min": round(float(agg.min()), 2),
                "max": round(float(agg.max()), 2),
                "mean": round(float(agg.mean()), 2),
            }
            continue

        latest = agg.iloc[-1]
        previous = agg.iloc[-2]
        abs_change = latest - previous
        pct_change = (abs_change / previous * 100) if previous != 0 else None

        summary[metric] = {
            "latest_period": str(periods[-1]),
            "previous_period": str(periods[-2]),
            "latest_value": round(float(latest), 2),
            "previous_value": round(float(previous), 2),
            "abs_change": round(float(abs_change), 2),
            "pct_change": round(float(pct_change), 2) if pct_change is not None else None,
            "min": round(float(agg.min()), 2),
            "max": round(float(agg.max()), 2),
            "mean": round(float(agg.mean()), 2),
        }

    return summary


def compute_segment_performance(df: pd.DataFrame, schema: Dict) -> List[Dict]:
    period_col = schema["period_col"]
    segment_cols = schema["segment_cols"]
    metric_cols = schema["metric_cols"]

    if not segment_cols or period_col is None:
        return []

    primary_segment = segment_cols[0]
    df_sorted = df.sort_values(period_col)
    latest_period = df_sorted[period_col].max()
    periods = sorted(df_sorted[period_col].unique())
    results = []

    prev_period = periods[-2] if len(periods) >= 2 else None

    for seg_value in df_sorted[primary_segment].unique():
        seg_data = {"segment_column": primary_segment, "segment_value": str(seg_value)}
        seg_metrics = {}

        for metric in metric_cols:
            latest_row = df_sorted[
                (df_sorted[primary_segment] == seg_value) &
                (df_sorted[period_col] == latest_period)
            ]
            latest_val = latest_row[metric].sum() if not latest_row.empty else 0

            if prev_period is not None:
                prev_row = df_sorted[
                    (df_sorted[primary_segment] == seg_value) &
                    (df_sorted[period_col] == prev_period)
                ]
                prev_val = prev_row[metric].sum() if not prev_row.empty else 0
                mom_change = ((latest_val - prev_val) / prev_val * 100) if prev_val != 0 else None
            else:
                prev_val = None
                mom_change = None

            seg_metrics[metric] = {
                "latest": round(float(latest_val), 2),
                "previous": round(float(prev_val), 2) if prev_val is not None else None,
                "mom_change_pct": round(float(mom_change), 2) if mom_change is not None else None,
            }

        seg_data["metrics"] = seg_metrics
        results.append(seg_data)

    # Add ranking
    for metric in metric_cols:
        values = [(r["segment_value"], r["metrics"][metric]["latest"]) for r in results]
        values.sort(key=lambda x: x[1], reverse=True)
        rank_map = {name: rank + 1 for rank, (name, _) in enumerate(values)}
        for r in results:
            r["metrics"][metric]["rank"] = rank_map[r["segment_value"]]

    return results


def detect_anomalies(df: pd.DataFrame, schema: Dict, z_threshold: float = 1.5) -> List[Dict]:
    """
    Advanced Multi-Method Anomaly Detection Engine:
      1. Z-Score Deviation: flags statistical outliers against normal distribution
      2. Severity Classification: Critical (|Z| >= 2.5), High (|Z| >= 2.0), Moderate (|Z| >= 1.5)
      3. IQR Outlier Bounds: Tukey's fences (Q1 - 1.5*IQR, Q3 + 1.5*IQR)
      4. Business Impact Metrics: % deviation from historical baseline mean
    """
    period_col = schema["period_col"]
    metric_cols = schema["metric_cols"]
    anomalies = []

    if period_col is None:
        return anomalies

    for metric in metric_cols:
        agg = df.groupby(period_col)[metric].sum().sort_index()
        if len(agg) < 3:
            continue

        mean_val = float(agg.mean())
        std_val = float(agg.std())
        if std_val == 0:
            continue

        q25 = float(agg.quantile(0.25))
        q75 = float(agg.quantile(0.75))
        iqr = q75 - q25
        lower_iqr = q25 - (1.5 * iqr)
        upper_iqr = q75 + (1.5 * iqr)

        for period, value in agg.items():
            val_float = float(value)
            z = (val_float - mean_val) / std_val
            abs_z = abs(z)

            is_z_outlier = abs_z >= z_threshold
            is_iqr_outlier = (val_float < lower_iqr) or (val_float > upper_iqr)

            if is_z_outlier or is_iqr_outlier:
                if abs_z >= 2.5:
                    severity = "Critical"
                elif abs_z >= 2.0:
                    severity = "High"
                else:
                    severity = "Moderate"

                dev_pct = ((val_float - mean_val) / mean_val * 100) if mean_val != 0 else 0

                anomalies.append({
                    "metric": metric,
                    "period": str(period),
                    "value": round(val_float, 2),
                    "z_score": round(float(z), 2),
                    "severity": severity,
                    "direction": "spike" if z > 0 else "dip",
                    "deviation_pct_from_mean": round(dev_pct, 1),
                    "is_iqr_outlier": is_iqr_outlier,
                    "explanation": f"Value {val_float:,.2f} deviated {dev_pct:+.1f}% from historical mean ({mean_val:,.2f}) with Z-score {z:+.2f}.",
                })

    return anomalies


def identify_top_bottom(segment_perf: List[Dict], metric_name: Optional[str] = None) -> Dict[str, Any]:
    if not segment_perf:
        return {"top": None, "bottom": None}

    first = segment_perf[0]
    if metric_name is None:
        metric_name = list(first["metrics"].keys())[0]

    scored = []
    for seg in segment_perf:
        m = seg["metrics"].get(metric_name, {})
        mom = m.get("mom_change_pct")
        scored.append({
            "segment": seg["segment_value"],
            "latest": m.get("latest"),
            "mom_change_pct": mom,
        })

    scored.sort(key=lambda x: x["mom_change_pct"] if x["mom_change_pct"] is not None else -9999, reverse=True)

    return {
        "metric": metric_name,
        "top_performer": scored[0] if scored else None,
        "bottom_performer": scored[-1] if scored else None,
    }


def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs the complete deterministic analysis pipeline."""
    schema = detect_schema(df)
    overall = compute_overall_summary(df, schema)
    segments = compute_segment_performance(df, schema)
    anomalies = detect_anomalies(df, schema)

    revenue_like = None
    for m in schema["metric_cols"]:
        if any(kw in m.lower() for kw in ["revenue", "sales", "spend", "volume", "order"]):
            revenue_like = m
            break
    top_bottom = identify_top_bottom(segments, revenue_like)

    return {
        "schema": schema,
        "overall_summary": overall,
        "segment_performance": segments,
        "anomalies": anomalies,
        "top_bottom": top_bottom,
    }

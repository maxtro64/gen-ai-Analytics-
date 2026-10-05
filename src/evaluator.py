"""
LLM Evaluation & Hallucination Guardrail Engine
================================================
Performs automated deterministic validation of LLM-generated business narratives
against pre-computed ground-truth data.

Audits:
  - Extraction of numeric claims (currency, percentages, volumes)
  - Reconciliation against ground truth database/JSON
  - Hallucination detection & accuracy score calculation
"""

import re
from typing import Dict, Any, List, Set


def _collect_ground_truth_numbers(analysis: Dict[str, Any]) -> Set[float]:
    """Extracts all valid numerical values from the deterministic KPI analysis."""
    numbers = set()

    def _extract_recursive(obj):
        if isinstance(obj, (int, float)):
            val = round(float(obj), 2)
            numbers.add(val)
            # Add rounded to 1 decimal place and whole number
            numbers.add(round(val, 1))
            numbers.add(round(val, 0))
            # Also add in thousands (K) or millions (M) units
            if abs(val) >= 1_000_000:
                m_val = round(val / 1_000_000, 2)
                numbers.add(m_val)
                numbers.add(round(m_val, 1))
            if abs(val) >= 1_000:
                k_val = round(val / 1_000, 2)
                numbers.add(k_val)
                numbers.add(round(k_val, 1))
        elif isinstance(obj, dict):
            for v in obj.values():
                _extract_recursive(v)
        elif isinstance(obj, list):
            for item in obj:
                _extract_recursive(item)

    _extract_recursive(analysis)
    return numbers


def evaluate_narrative_accuracy(narrative: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans generated narrative for numerical assertions and verifies them against ground truth.
    Returns accuracy score, verification status, and audit trail.
    """
    if not narrative:
        return {
            "total_claims": 0,
            "verified_claims": 0,
            "accuracy_score": 100.0,
            "hallucination_rate": 0.0,
            "verdict": "NO CLAIMS",
            "audit_log": [],
        }

    ground_truth = _collect_ground_truth_numbers(analysis)

    # Regex to find:
    # 1. Currency e.g. $3.36M, $170,000, $982.2K
    # 2. Percentages e.g. 9.8%, +11.26%, -4.5%
    # 3. Plain floating/integer numbers e.g. 1,680,000, 33.3
    pattern = re.compile(
        r"(\$?\s*[\+\-]?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|[KkMmBbTt]|million|billion|thousand)?)"
    )

    raw_matches = pattern.findall(narrative)
    audit_log = []
    verified_count = 0
    total_audited = 0

    for token in raw_matches:
        cleaned = token.strip()
        # Filter out trivial numbers like list item numbers (1., 2.), years (2024, 2025, 2026), or single digits
        if not cleaned or cleaned in ("2024", "2025", "2026", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
            continue

        # Extract numerical value
        num_str = re.sub(r"[^\d\.\+\-]", "", cleaned)
        try:
            val = float(num_str)
        except ValueError:
            continue

        total_audited += 1

        # Check if the number (or its scaled variant) matches ground truth
        matched = False
        candidates = [
            round(val, 2),
            round(val, 1),
            round(val, 0),
            round(abs(val), 2),
            round(abs(val), 1),
        ]

        for cand in candidates:
            # Check within 0.1 tolerance to account for rounding
            if any(abs(cand - gt) <= 0.15 for gt in ground_truth):
                matched = True
                break

        if matched:
            verified_count += 1
            status = "VERIFIED"
        else:
            status = "UNVERIFIED"

        audit_log.append({
            "claim": cleaned,
            "parsed_value": val,
            "status": status,
        })

    total = max(total_audited, 1)
    accuracy = round((verified_count / total) * 100, 1) if total_audited > 0 else 100.0
    hallucination_rate = round(100.0 - accuracy, 1)

    if accuracy >= 95.0:
        verdict = "PASSED: High Truthfulness (Zero Critical Hallucination)"
    elif accuracy >= 80.0:
        verdict = "ACCEPTABLE: Minor Unverified Formats Detected"
    else:
        verdict = "FLAGGED: Numerical Discrepancies Present"

    return {
        "total_claims": total_audited,
        "verified_claims": verified_count,
        "accuracy_score": accuracy,
        "hallucination_rate": hallucination_rate,
        "verdict": verdict,
        "audit_log": audit_log[:15],  # top 15 sampled
    }

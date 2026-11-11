"""Utilities for turning benchmark runs into publication-friendly tables."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def format_metric_table(rows: list[dict[str, Any]]) -> str:
    """Render a markdown table for variant comparisons."""
    if not rows:
        return "| variant | case_count | exact_match_rate | policy_violation_rate | intervention_rate |\n| --- | --- | --- | --- | --- |"

    headers = [
        "variant",
        "case_count",
        "exact_match_rate",
        "policy_violation_rate",
        "intervention_rate",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("variant", "")),
                    str(row.get("case_count", 0)),
                    f"{float(row.get('exact_match_rate', 0.0)):.4f}",
                    f"{float(row.get('policy_violation_rate', 0.0)):.4f}",
                    f"{float(row.get('intervention_rate', 0.0)):.4f}",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def summarize_best_variant(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Select the best-performing variant by exact match rate and return a paper summary."""
    if not rows:
        return None
    best = max(rows, key=lambda row: float(row.get("exact_match_rate", 0.0)))
    exact_rates = [float(row.get("exact_match_rate", 0.0)) for row in rows]
    return {
        "best_variant": best.get("variant", ""),
        "best_exact_match_rate": float(best.get("exact_match_rate", 0.0)),
        "average_exact_match_rate": round(mean(exact_rates), 4),
        "stddev_exact_match_rate": round(pstdev(exact_rates), 4) if len(exact_rates) > 1 else 0.0,
    }


def summarize_variant_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a brief descriptive statistics summary for paper reporting."""
    if not rows:
        return {"exact_match_mean": 0.0, "exact_match_stddev": 0.0, "exact_match_range": [0.0, 0.0]}
    exact_rates = [float(row.get("exact_match_rate", 0.0)) for row in rows]
    return {
        "exact_match_mean": round(mean(exact_rates), 4),
        "exact_match_stddev": round(pstdev(exact_rates), 4) if len(exact_rates) > 1 else 0.0,
        "exact_match_range": [round(min(exact_rates), 4), round(max(exact_rates), 4)],
    }

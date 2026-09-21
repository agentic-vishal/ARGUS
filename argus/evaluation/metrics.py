"""Deterministic evaluation metrics for ARGUS benchmark runs."""

from __future__ import annotations

from typing import Any

METRIC_NAMES = (
    "retrieval_precision", "claim_grounding", "contradiction_recall", "tool_selection_accuracy",
    "citation_coverage", "risk_classification", "cascade_efficiency", "latency", "cost",
)


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 1.0


def retrieval_precision(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    return _ratio(sum(item in relevant_ids for item in retrieved_ids), len(retrieved_ids))


def claim_grounding(claims: list[dict[str, Any]]) -> float:
    return _ratio(sum(bool(item.get("sources")) and item.get("confidence", 0) > 0 for item in claims), len(claims))


def contradiction_recall(detected: list[dict[str, Any]], expected: int) -> float:
    return _ratio(min(len(detected), expected), expected)


def tool_selection_accuracy(selected: list[str], expected: set[str]) -> float:
    return _ratio(sum(item in expected for item in selected), len(selected))


def citation_coverage(claims: list[dict[str, Any]]) -> float:
    return _ratio(sum(bool(item.get("sources")) for item in claims), len(claims))


def risk_classification(actual: str, expected: str) -> float:
    return 1.0 if actual.lower() == expected.lower() else 0.0


def cascade_efficiency(telemetry: dict[str, Any]) -> float:
    total = telemetry.get("call_count", 0)
    low_cost = telemetry.get("tiers", {}).get("tier_1", 0) + telemetry.get("tiers", {}).get("tier_2", 0)
    return _ratio(low_cost, total)


def evaluate_run(result: dict[str, Any], expected: dict[str, Any] | None = None) -> dict[str, float]:
    expected = expected or {}
    metrics = {
        "retrieval_precision": retrieval_precision(result.get("retrieved_ids", []), set(expected.get("relevant_ids", []))),
        "claim_grounding": claim_grounding(result.get("verified_claims", [])),
        "contradiction_recall": contradiction_recall(result.get("conflicting_claims", []), int(expected.get("expected_contradictions", len(result.get("conflicting_claims", []))))),
        "tool_selection_accuracy": tool_selection_accuracy(result.get("selected_tools", []), set(expected.get("expected_tools", result.get("selected_tools", [])))),
        "citation_coverage": citation_coverage(result.get("verified_claims", [])),
        "risk_classification": risk_classification(result.get("risk_level", "unknown"), expected.get("risk_level", result.get("risk_level", "unknown"))),
        "cascade_efficiency": cascade_efficiency(result.get("model_telemetry", {})),
        "latency": float(result.get("latency_ms", result.get("model_telemetry", {}).get("total_latency_ms", 0.0))),
        "cost": float(result.get("cost", result.get("model_telemetry", {}).get("total_estimated_cost", 0.0))),
    }
    return metrics


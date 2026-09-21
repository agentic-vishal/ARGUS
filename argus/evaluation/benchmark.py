"""Benchmark runner for deterministic scenario-level checks."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from argus.evaluation.metrics import evaluate_run
from argus.evaluation.scenarios import SCENARIOS, BenchmarkScenario


def run_benchmarks(run: Callable[[BenchmarkScenario], dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for scenario in SCENARIOS:
        output = run(scenario)
        results.append({"scenario": asdict(scenario), "metrics": evaluate_run(output, {"expected_contradictions": scenario.expected_contradictions, "risk_level": scenario.expected_risk}), "output": output})
    return results


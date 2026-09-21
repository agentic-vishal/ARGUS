"""Conditional routing policies for the investigation graph."""

from argus.config.settings import Settings
from argus.graph.state import IntelligenceState
from argus.guardrails.budgets import budget_exhausted
from argus.guardrails.evidence import evidence_sufficient


def next_step(state: IntelligenceState, settings: Settings) -> str:
    if budget_exhausted(state, settings):
        return "risk_assessment_with_uncertainty"
    if evidence_sufficient(state, settings):
        return "risk_assessment"
    return "continue_research"


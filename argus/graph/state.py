"""Shared LangGraph-compatible state contract from the ARGUS blueprint."""

from typing import Any, TypedDict


class IntelligenceState(TypedDict, total=False):
    user_query: str
    investigation_objective: str
    entities: list[str]
    companies: list[str]
    countries: list[str]
    internal_documents: list[dict[str, Any]]
    news_articles: list[dict[str, Any]]
    government_sources: list[dict[str, Any]]
    market_signals: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    conflicting_claims: list[dict[str, Any]]
    verified_claims: list[dict[str, Any]]
    impacted_products: list[str]
    impacted_suppliers: list[str]
    impacted_regions: list[str]
    missing_information: list[str]
    investigation_iterations: int
    risk_score: float
    confidence_score: float
    evidence_quality_score: float
    recommended_actions: list[dict[str, Any]]
    final_report: str
    research_plan: list[str]
    evidence: list[dict[str, Any]]
    evaluation_results: dict[str, Any]
    risk_assessment: dict[str, Any]
    exposure_matches: list[dict[str, Any]]
    route: str
    termination_reason: str
    tool_errors: list[str]
    requires_human_approval: bool
    react_iterations: int
    react_tool_calls: int
    react_trace: list[dict[str, Any]]
    last_action: str
    last_observation: dict[str, Any]
    next_action: str
    research_budget_remaining: int
    model_telemetry: dict[str, Any]
    unsupported_claims: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    approval_requests: list[dict[str, Any]]
    overrides: list[dict[str, Any]]


def initial_state(user_query: str) -> IntelligenceState:
    """Create a deterministic empty state suitable for graph initialization."""
    return {
        "user_query": user_query,
        "investigation_objective": user_query,
        "entities": [],
        "companies": [],
        "countries": [],
        "internal_documents": [],
        "news_articles": [],
        "government_sources": [],
        "market_signals": [],
        "claims": [],
        "conflicting_claims": [],
        "verified_claims": [],
        "impacted_products": [],
        "impacted_suppliers": [],
        "impacted_regions": [],
        "missing_information": [],
        "investigation_iterations": 0,
        "risk_score": 0.0,
        "confidence_score": 0.0,
        "evidence_quality_score": 0.0,
        "recommended_actions": [],
        "final_report": "",
        "research_plan": [],
        "evidence": [],
        "evaluation_results": {},
        "risk_assessment": {},
        "exposure_matches": [],
        "route": "",
        "termination_reason": "",
        "tool_errors": [],
        "requires_human_approval": False,
        "react_iterations": 0,
        "react_tool_calls": 0,
        "react_trace": [],
        "last_action": "",
        "last_observation": {},
        "next_action": "",
        "research_budget_remaining": 0,
        "model_telemetry": {},
        "unsupported_claims": [],
        "audit_events": [],
        "approvals": [],
        "approval_requests": [],
        "overrides": [],
    }

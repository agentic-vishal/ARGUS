"""Concise executive report renderer with explicit evidence boundaries."""

from typing import Any


def generate_executive_report(state: dict[str, Any]) -> str:
    risk = state.get("risk_assessment", {})
    facts = [item.get("claim", "") for item in state.get("verified_claims", []) if item.get("contradiction_status") == "none"]
    inference = [item.get("rationale", "") for item in state.get("exposure_matches", [])]
    uncertainty = list(state.get("missing_information", []))
    conflicts = state.get("conflicting_claims", [])
    evidence = sorted({ref for claim in state.get("verified_claims", []) for ref in claim.get("sources", [])})
    actions = state.get("recommended_actions", [])
    lines = [
        "ARGUS GLOBAL RISK INTELLIGENCE REPORT",
        "",
        f"Question: {state.get('user_query', '')}",
        "",
        "FACTS",
        *([f"- {fact}" for fact in facts] or ["- No fully verified non-conflicting facts."]),
        "",
        "INFERENCE / BUSINESS EXPOSURE",
        *([f"- {item}" for item in inference] or ["- No internal exposure was mapped."]),
        "",
        "RISK",
        f"- Composite risk: {risk.get('risk_score', state.get('risk_score', 0.0))}/10",
        f"- Impact: {risk.get('impact', 'unknown')}/10; Probability: {risk.get('probability', 'unknown')}/10; Urgency: {risk.get('urgency', 'unknown')}/10",
        "",
        "CONFIDENCE",
        f"- {round(float(risk.get('confidence', state.get('confidence_score', 0.0))) * 100)}%",
        "",
        "EVIDENCE",
        *([f"- {ref}" for ref in evidence] or ["- No evidence references recorded."]),
        "",
        "UNCERTAINTY",
        *([f"- {item}" for item in uncertainty] or ["- No known information gaps."]),
        "",
        "UNRESOLVED CONFLICTS",
        *([f"- {item.get('claim_type')}: {', '.join(item.get('contradiction_types', []))}" for item in conflicts] or ["- None identified."]),
        "",
        "RECOMMENDED ACTIONS",
        *([f"- [{item.get('priority', '?')}] {item.get('action')} - owner: {item.get('owner')}; urgency: {item.get('urgency', 'unspecified')}" for item in actions] or ["- None generated."]),
    ]
    return "\n".join(lines)

"""Small, deterministic workflow nodes for the ARGUS investigation lifecycle.

Each function accepts state plus an explicit dependency container and returns only
a partial state update, which makes it straightforward to unit test or replace
with an LLM-backed implementation.
"""

from __future__ import annotations

import re
from typing import Any

from argus.analysis.exposure import analyze_exposure
from argus.analysis.recommendations import generate_recommendations
from argus.analysis.report import generate_executive_report
from argus.analysis.risk import score_risk
from argus.graph.dependencies import WorkflowDependencies
from argus.graph.state import IntelligenceState
from argus.guardrails.approval import ApprovalGate
from argus.guardrails.evidence import reject_unsupported_claims
from argus.models.evidence import detect_contradictions, extract_attributes, source_provenance
from argus.models.schemas import Claim


def _append_error(state: IntelligenceState, error: Exception) -> list[str]:
    return [*state.get("tool_errors", []), str(error)]


def _as_dict(value: Any) -> dict[str, Any]:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def query_analysis_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    query = state.get("user_query", "").strip()
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", query)
    return {
        "investigation_objective": query,
        "entities": list(dict.fromkeys(words))[:20],
        "missing_information": [] if query else ["user_query"],
    }


def supervisor_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    return {"research_plan": [
        "discover external news and regulatory evidence",
        "retrieve internal supplier, product, and policy context",
        "extract and verify material claims",
        "map verified events to organizational exposure",
        "score risk and produce approved recommendations",
    ]}


def external_discovery_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    query = state.get("investigation_objective", state.get("user_query", ""))
    errors = state.get("tool_errors", [])
    try:
        news = deps.news.search_news(query)
    except Exception as exc:  # noqa: BLE001 - external adapter failures are recorded
        news, errors = [], _append_error(state, exc)
    try:
        regulations = deps.government.search_regulation(query)
    except Exception as exc:  # noqa: BLE001 - external adapter failures are recorded
        regulations, errors = [], [*errors, str(exc)]
    return {
        "news_articles": [_as_dict(item) for item in news],
        "government_sources": [_as_dict(item) for item in regulations],
        "investigation_iterations": state.get("investigation_iterations", 0) + 1,
        "tool_errors": errors,
    }


def internal_retrieval_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    query = state.get("investigation_objective", state.get("user_query", ""))
    try:
        filters = {"active": True, **deps.access_policy.retrieval_filters()}
        results = deps.retriever.search(query, filters=filters, limit=10)
        documents = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in results]
        return {"internal_documents": documents}
    except Exception as exc:  # noqa: BLE001 - retrieval failures are recorded
        return {"internal_documents": [], "tool_errors": _append_error(state, exc)}


def _claim_from_record(record: dict[str, Any], index: int, source_type: str) -> Claim:
    text = str(record.get("claim") or record.get("summary") or record.get("title") or record.get("content") or "").strip()
    provenance = source_provenance(record, source_type, index)
    return Claim(
        claim_id=str(record.get("claim_id") or f"{source_type}_{index}"),
        claim=text or "Unspecified material claim",
        claim_type=str(record.get("claim_type") or source_type),
        sources=[provenance.source_id],
        primary_source=provenance.is_primary,
        source_authority=provenance.authority_score,
        recency_score=float(record.get("recency_score", 0.5)),
        attributes=extract_attributes(text, record),
        provenance=[provenance],
        confidence=float(record.get("confidence", 0.5)),
    )


def claim_extraction_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    records = (
        [(item, "news") for item in state.get("news_articles", [])]
        + [(item, "government") for item in state.get("government_sources", [])]
        + [(item, "internal") for item in state.get("internal_documents", [])]
    )
    claims = [_claim_from_record(record, index, source_type).model_dump(mode="json") for index, (record, source_type) in enumerate(records)]
    missing = list(state.get("missing_information", []))
    if not claims:
        missing.append("independent evidence")
    return {"claims": claims, "missing_information": list(dict.fromkeys(missing))}


def verification_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    verified = []
    all_claims = [Claim.model_validate(raw) for raw in state.get("claims", [])]
    support: dict[str, set[str]] = {}
    for item in all_claims:
        key = re.sub(r"\W+", " ", item.claim.lower()).strip()
        support.setdefault(key, set()).update(item.sources)
    for claim in all_claims:
        key = re.sub(r"\W+", " ", claim.claim.lower()).strip()
        provenance_authority = max((source.authority_score for source in claim.provenance), default=claim.source_authority)
        primary_regulatory = any(source.is_primary and source.source_type in {"government", "regulatory", "official_notice"} for source in claim.provenance)
        # Primary regulatory evidence receives the highest authority weight, but does not erase disagreement.
        authority = max(provenance_authority, 1.0 if primary_regulatory else 0.0)
        corroboration = min(1.0, len(support.get(key, set())) / 3)
        confidence = min(1.0, (authority * 0.50) + (claim.recency_score * 0.20) + (corroboration * 0.30))
        claim = claim.model_copy(update={
            "corroboration_score": corroboration,
            "source_authority": authority,
            "confidence": confidence,
        })
        verified.append(claim.model_dump(mode="json"))
    confidence = sum(item["confidence"] for item in verified) / len(verified) if verified else 0.0
    missing = list(state.get("missing_information", []))
    if not any(
        source.is_primary and source.source_type in {"government", "regulatory", "official_notice"}
        for item in all_claims for source in item.provenance
    ):
        missing.append("authoritative primary source for regulatory facts")
    return {
        "verified_claims": verified,
        "confidence_score": confidence,
        "evidence_quality_score": confidence,
        "missing_information": list(dict.fromkeys(missing)),
    }


def contradiction_detection_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    # Accept compact state records as well as fully normalized Claim payloads.
    # This is useful at graph boundaries where a caller may provide claims
    # before the extraction/verification nodes have enriched them.
    claims = [
        Claim.model_validate({**raw, "claim_id": raw.get("claim_id") or f"claim_{index}"})
        for index, raw in enumerate(state.get("verified_claims", []))
    ]
    conflicts = detect_contradictions(claims)
    conflicting_ids = {claim["claim_id"] for conflict in conflicts for claim in conflict["claims"]}
    types_by_id = {
        claim_id: sorted({kind for conflict in conflicts if claim_id in {item["claim_id"] for item in conflict["claims"]} for kind in conflict["contradiction_types"]})
        for claim_id in conflicting_ids
    }
    updated = []
    for claim in claims:
        types = types_by_id.get(claim.claim_id, [])
        updated.append(claim.model_copy(update={
            "contradiction": bool(types),
            "contradiction_status": "unresolved" if types else "none",
            "contradiction_types": types,
            "contradiction_details": [f"Unresolved {kind} disagreement" for kind in types],
        }).model_dump(mode="json"))
    missing = list(state.get("missing_information", []))
    for conflict in conflicts:
        missing.append(f"resolve {', '.join(conflict['contradiction_types'])} contradiction for {conflict['claim_type']}")
    return {"verified_claims": updated, "conflicting_claims": conflicts, "missing_information": list(dict.fromkeys(missing))}


def evidence_sufficiency_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    iterations = state.get("investigation_iterations", 0)
    if iterations >= deps.settings.max_investigation_iterations:
        route, reason = "budget_exit", "research budget exhausted"
    elif state.get("missing_information") or state.get("confidence_score", 0.0) < deps.settings.min_confidence or state.get("conflicting_claims"):
        route, reason = "retry", "evidence is insufficient or contradictory"
    else:
        route, reason = "normal_completion", "evidence gate passed"
    return {"route": route, "termination_reason": reason}


def exposure_analysis_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    matches = analyze_exposure(state)
    suppliers = sorted({str(item.get("supplier")) for item in matches if item.get("supplier")})
    products = sorted({str(item.get("product")) for item in matches if item.get("product")})
    regions = sorted({str(item.get("region")) for item in matches if item.get("region")})
    return {"exposure_matches": matches, "impacted_suppliers": suppliers, "impacted_products": products, "impacted_regions": regions, "countries": regions}


def risk_assessment_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    assessment = score_risk(state)
    return {"risk_score": assessment["risk_score"], "risk_assessment": assessment}


def recommendation_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    actions = generate_recommendations(state)
    approval_requests = [ApprovalGate().request(action) for action in actions if action.get("requires_approval")]
    return {
        "recommended_actions": actions,
        "requires_human_approval": any(action.get("requires_approval", True) for action in actions),
        "approval_requests": approval_requests,
    }


def evaluation_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    grounding = reject_unsupported_claims(state)
    unsupported = grounding["unsupported_claims"]
    checks = {
        "claims_have_sources": not unsupported,
        "contradictions_surfaced": True,
        "recommendations_present": bool(state.get("recommended_actions")),
        "unsupported_claim_count": len(unsupported),
    }
    if state.get("investigation_iterations", 0) >= deps.settings.max_investigation_iterations:
        route = "budget_exit"
    elif unsupported:
        route = "retry"
    else:
        route = "normal_completion"
    return {**grounding, "evaluation_results": checks, "route": route}


def final_report_node(state: IntelligenceState, deps: WorkflowDependencies) -> dict[str, Any]:
    return {"final_report": generate_executive_report(state)}

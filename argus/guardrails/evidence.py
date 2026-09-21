"""Evidence sufficiency policy seam."""

from argus.config.settings import Settings
from argus.graph.state import IntelligenceState


def evidence_sufficient(state: IntelligenceState, settings: Settings) -> bool:
    return (
        state.get("confidence_score", 0.0) >= settings.min_confidence
        and not state.get("missing_information")
        and not state.get("conflicting_claims")
    )


def grounded_claims(state: IntelligenceState) -> tuple[list[dict], list[dict]]:
    """Split claims into grounded and unsupported records using source references."""
    evidence_ids = {item.get("evidence_id", item.get("source_id")) for item in state.get("evidence", [])}
    for collection in ("news_articles", "government_sources", "internal_documents"):
        evidence_ids.update(item.get("source_id", item.get("id", item.get("document_id", item.get("article_id")))) for item in state.get(collection, []))
    evidence_ids.discard(None)
    grounded, unsupported = [], []
    for claim in state.get("claims", []):
        refs = set(claim.get("sources", []))
        target = grounded if refs and refs & evidence_ids else unsupported
        target.append(claim)
    return grounded, unsupported


def reject_unsupported_claims(state: IntelligenceState) -> dict:
    grounded, unsupported = grounded_claims(state)
    missing = list(state.get("missing_information", []))
    if unsupported:
        missing.append(f"grounding for {len(unsupported)} unsupported material claim(s)")
    return {"claims": grounded, "unsupported_claims": unsupported, "missing_information": list(dict.fromkeys(missing))}

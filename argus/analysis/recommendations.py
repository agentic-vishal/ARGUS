"""Recommendation generation only; deliberately contains no execution methods."""

from pydantic import BaseModel, Field

from argus.guardrails.approval import requires_approval


class PrioritizedAction(BaseModel):
    action: str
    owner: str
    urgency: str
    priority: int = Field(ge=1, le=5)
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    requires_approval: bool = True


def generate_recommendations(state: dict) -> list[dict]:
    risk = state.get("risk_assessment", {})
    refs = risk.get("evidence_refs", [])
    actions: list[PrioritizedAction] = []
    if state.get("impacted_suppliers") or state.get("exposure_matches"):
        actions.append(PrioritizedAction(action="Validate supplier commitments, inventory, and alternate capacity", owner="procurement", urgency="immediate", priority=1, rationale="Supplier exposure is supported by mapped internal records.", evidence_refs=refs))
    if any(item.get("obligations") for item in state.get("exposure_matches", [])):
        actions.append(PrioritizedAction(action="Review contracts, regulatory obligations, and notification requirements", owner="legal", urgency="immediate", priority=1, rationale="Mapped contracts or obligations may create time-sensitive duties.", evidence_refs=refs))
    actions.append(PrioritizedAction(action="Monitor authoritative external updates and refresh the assessment", owner="risk", urgency="near_term", priority=2, rationale="Confidence and unresolved contradictions require continued monitoring.", evidence_refs=refs, requires_approval=False))
    results = [item.model_dump(mode="json") for item in sorted(actions, key=lambda item: item.priority)]
    for item in results:
        item["requires_approval"] = requires_approval(item)
    return results

"""Human approval gates for consequential recommendations."""

from typing import Any

APPROVAL_TERMS = ("supplier communication", "contact supplier", "procurement", "legal", "external write", "execute")


def requires_approval(action: dict[str, Any]) -> bool:
    if action.get("requires_approval", False):
        return True
    text = f"{action.get('action', '')} {action.get('owner', '')}".lower()
    return any(term in text for term in APPROVAL_TERMS)


class ApprovalGate:
    def request(self, action: dict[str, Any]) -> dict[str, Any]:
        return {"action": action.get("action", ""), "status": "pending", "requires_approval": requires_approval(action)}

    def approve(self, request: dict[str, Any], approver: str, rationale: str = "") -> dict[str, Any]:
        return {**request, "status": "approved", "approver": approver, "rationale": rationale}

    def override(self, request: dict[str, Any], approver: str, rationale: str) -> dict[str, Any]:
        return {**request, "status": "overridden", "approver": approver, "rationale": rationale}

"""Map verified external claims to internal enterprise exposure."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExposureMatch(BaseModel):
    claim_id: str
    document_id: str
    match_type: str
    supplier: str | None = None
    product: str | None = None
    region: str | None = None
    contract: str | None = None
    obligations: list[str] = Field(default_factory=list)
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)


def _values(claim: dict[str, Any]) -> set[str]:
    attrs = claim.get("attributes", {})
    values: list[Any] = [claim.get("claim", ""), attrs.get("scope"), attrs.get("entities"), attrs.get("countries"), attrs.get("products")]
    result: set[str] = set()
    for value in values:
        if isinstance(value, list):
            result.update(str(item).lower() for item in value)
        elif value:
            result.add(str(value).lower())
    return result


def analyze_exposure(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return traceable claim-to-enterprise matches without making decisions."""
    matches: list[ExposureMatch] = []
    documents = state.get("internal_documents", [])
    claims = state.get("verified_claims", [])
    for claim in claims:
        claim_values = _values(claim)
        for document in documents:
            searchable = " ".join(str(document.get(key, "")) for key in ("supplier", "product", "region", "contract", "obligation", "text", "content")).lower()
            direct_keys = [key for key in ("supplier", "product", "region", "contract") if document.get(key) and str(document[key]).lower() in claim_values]
            semantic_hit = bool(direct_keys) or any(token in searchable for token in claim_values if len(token) > 3)
            if not semantic_hit:
                continue
            obligations = document.get("obligations", [])
            if isinstance(obligations, str):
                obligations = [obligations]
            matches.append(ExposureMatch(
                claim_id=claim.get("claim_id", ""), document_id=document.get("document_id", document.get("source_id", "")),
                match_type=";".join(direct_keys) or "text_match",
                supplier=document.get("supplier"), product=document.get("product"), region=document.get("region"),
                contract=document.get("contract") or document.get("contract_id"), obligations=obligations,
                rationale="Verified claim terms overlap with current internal enterprise records.",
                evidence_refs=[
                    ref
                    for ref in [
                        claim.get("claim_id", ""),
                        *claim.get("sources", []),
                        document.get("document_id", document.get("source_id", "")),
                    ]
                    if ref
                ],
            ))
    return [match.model_dump(mode="json") for match in matches]

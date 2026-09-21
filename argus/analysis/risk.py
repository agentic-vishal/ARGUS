"""Transparent, independently displayed risk dimensions."""

from pydantic import BaseModel, Field


class RiskDimensions(BaseModel):
    impact: float = Field(ge=0, le=10)
    probability: float = Field(ge=0, le=10)
    urgency: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=10)
    formula: str
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: str


def score_risk(state: dict) -> dict:
    exposure = state.get("exposure_matches", [])
    claims = state.get("verified_claims", [])
    conflicts = state.get("conflicting_claims", [])
    confidence = float(state.get("confidence_score", 0.0))
    impact = min(10.0, 2.0 + len({item.get("product") for item in exposure if item.get("product")}) * 2.0 + len({item.get("supplier") for item in exposure if item.get("supplier")})) if claims else 0.0
    probability = min(10.0, 2.0 + len(exposure) * 1.5) if claims else 0.0
    urgency = min(10.0, 4.0 + (2.0 if conflicts else 0.0) + (2.0 if any(item.get("obligations") for item in exposure) else 0.0)) if claims else 0.0
    risk_score = round((impact * 0.4) + (probability * 0.35) + (urgency * 0.25), 2)
    evidence_refs = sorted({ref for item in exposure for ref in item.get("evidence_refs", [])})
    return RiskDimensions(
        impact=impact, probability=probability, urgency=urgency, confidence=confidence,
        risk_score=risk_score,
        formula="risk_score = 0.40*impact + 0.35*probability + 0.25*urgency; confidence is displayed separately",
        evidence_refs=evidence_refs,
        rationale="Dimensions are based on verified claims, mapped enterprise exposure, obligations, and unresolved conflicts.",
    ).model_dump(mode="json")

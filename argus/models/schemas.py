"""Stable domain schemas shared by graph nodes and adapters."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceProvenance(BaseModel):
    source_id: str
    source_type: str
    title: str | None = None
    uri: str | None = None
    publisher: str | None = None
    is_primary: bool = False
    authority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    published_at: datetime | None = None
    retrieved_at: datetime | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    source_id: str
    source_type: str
    title: str | None = None
    uri: str | None = None
    content: str = ""
    published_at: datetime | None = None
    authority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    provenance: list[SourceProvenance] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim: str
    claim_type: str
    sources: list[str] = Field(default_factory=list)
    primary_source: bool = False
    source_authority: float = Field(default=0.0, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    corroboration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction: bool = False
    contradiction_status: Literal["none", "unresolved", "resolved_prefer_primary"] = "none"
    contradiction_types: list[Literal["date", "scope", "entity", "severity", "causality"]] = Field(default_factory=list)
    contradiction_details: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenance: list[SourceProvenance] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RiskAssessment(BaseModel):
    impact: float = Field(ge=0.0, le=10.0)
    probability: float = Field(ge=0.0, le=10.0)
    urgency: float = Field(ge=0.0, le=10.0)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=10.0)
    rationale: str = ""


class Recommendation(BaseModel):
    action: str
    owner: str
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    rationale: str = ""
    requires_approval: bool = True

"""Evidence normalization, authority scoring, and contradiction detection."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from argus.models.schemas import Claim, SourceProvenance

AUTHORITY_BY_SOURCE = {
    "government": 1.0,
    "regulatory": 1.0,
    "official_notice": 1.0,
    "contract": 0.95,
    "internal": 0.85,
    "supplier": 0.75,
    "news": 0.55,
    "market": 0.5,
}


def source_provenance(record: dict[str, Any], source_type: str, index: int) -> SourceProvenance:
    source_id = str(record.get("source_id") or record.get("id") or record.get("document_id") or record.get("article_id") or f"{source_type}_{index}")
    source_kind = str(record.get("source_type") or source_type)
    is_primary = bool(record.get("primary_source", source_kind in {"government", "regulatory", "official_notice"}))
    authority = float(record.get("authority_score", AUTHORITY_BY_SOURCE.get(source_kind, 0.5)))
    published = record.get("published_at") or record.get("source_date")
    if isinstance(published, str):
        try:
            published = datetime.fromisoformat(published)
        except ValueError:
            published = None
    return SourceProvenance(
        source_id=source_id,
        source_type=source_kind,
        title=record.get("title"),
        uri=record.get("uri") or record.get("url") or record.get("source_url"),
        publisher=record.get("publisher") or record.get("source"),
        is_primary=is_primary,
        authority_score=authority,
        published_at=published if isinstance(published, datetime) else None,
    )


def extract_attributes(text: str, record: dict[str, Any]) -> dict[str, Any]:
    """Extract contradiction-relevant facets while preserving source-provided fields."""
    attrs = dict(record.get("attributes") or {})
    for key in ("effective_date", "date", "scope", "entities", "severity", "causality", "countries", "products"):
        if key in record:
            attrs[key] = record[key]
    date_match = re.search(r"(?:effective|begin|start|starts|take effect)[^\d]*(\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2})", text)
    if date_match and "effective_date" not in attrs:
        attrs["effective_date"] = date_match.group(1)
    return attrs


def contradiction_types(left: Claim, right: Claim) -> list[str]:
    types: list[str] = []
    keys = {
        "effective_date": "date", "date": "date", "scope": "scope", "entities": "entity",
        "countries": "scope", "products": "scope", "severity": "severity", "causality": "causality",
    }
    for key, kind in keys.items():
        left_value, right_value = left.attributes.get(key), right.attributes.get(key)
        if (
            left_value is not None
            and right_value is not None
            and str(left_value).lower() != str(right_value).lower()
            and kind not in types
        ):
            types.append(kind)
    if not types and left.claim.strip().lower() != right.claim.strip().lower():
        types.append("scope")
    return types


def detect_contradictions(claims: list[Claim]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        grouped[claim.claim_type].append(claim)
    conflicts: list[dict[str, Any]] = []
    for claim_type, group in grouped.items():
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                types = contradiction_types(left, right)
                if types:
                    conflicts.append({
                        "claim_type": claim_type,
                        "contradiction_types": types,
                        "claims": [left.model_dump(mode="json"), right.model_dump(mode="json")],
                        "status": "unresolved",
                        "resolution": "Prefer authoritative primary evidence for regulatory facts; preserve disagreement until verified.",
                    })
    return conflicts

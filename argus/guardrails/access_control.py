"""Access-control seam for internal retrieval."""

from typing import Any

from pydantic import BaseModel, Field


class AccessPolicy(BaseModel):
    allowed_confidentiality: set[str] = Field(default_factory=lambda: {"public", "internal"})
    allowed_regions: set[str] | None = None
    allowed_document_types: set[str] | None = None

    def retrieval_filters(self) -> dict[str, Any]:
        filters: dict[str, Any] = {"confidentiality": self.allowed_confidentiality}
        if self.allowed_regions:
            filters["region"] = self.allowed_regions
        if self.allowed_document_types:
            filters["document_type"] = self.allowed_document_types
        return filters


def filter_metadata(metadata: dict[str, Any], allowed_confidentiality: set[str]) -> bool:
    return metadata.get("confidentiality", "public") in allowed_confidentiality


def can_retrieve(metadata: dict[str, Any], policy: AccessPolicy) -> bool:
    return (
        filter_metadata(metadata, policy.allowed_confidentiality)
        and not (policy.allowed_regions and metadata.get("region") not in policy.allowed_regions)
        and not (
            policy.allowed_document_types
            and metadata.get("document_type") not in policy.allowed_document_types
        )
    )


def filter_before_retrieval(query: str, metadata: dict[str, Any], policy: AccessPolicy) -> tuple[str, dict[str, Any]] | None:
    """Return a safe query/metadata pair, or None before the retriever is called."""
    return (query, metadata) if can_retrieve(metadata, policy) else None

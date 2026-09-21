"""Document ingestion pipeline."""

from typing import Any

from argus.rag.cleaning import clean_text
from argus.rag.enrichment import enrich_metadata
from argus.rag.models import EnterpriseDocument


def normalize_document(document: str, metadata: dict[str, Any] | None = None, *, document_id: str = "document") -> EnterpriseDocument:
    return EnterpriseDocument(
        document_id=document_id,
        text=clean_text(document),
        metadata=enrich_metadata(document_id, metadata or {}),
    )

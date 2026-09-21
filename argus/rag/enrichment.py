"""Metadata normalization and enrichment."""

from datetime import date
from typing import Any

from argus.rag.models import DocumentMetadata


def enrich_metadata(document_id: str, metadata: dict[str, Any]) -> DocumentMetadata:
    values = dict(metadata)
    values["document_id"] = document_id
    values["document_type"] = values.get("document_type", "unknown")
    values["confidentiality"] = values.get("confidentiality", "internal")
    for key in ("valid_from", "valid_until", "source_date"):
        if isinstance(values.get(key), str):
            values[key] = date.fromisoformat(values[key])
    known = set(DocumentMetadata.model_fields)
    values["extra"] = {**values.get("extra", {}), **{k: v for k, v in values.items() if k not in known}}
    return DocumentMetadata.model_validate({k: v for k, v in values.items() if k in known})


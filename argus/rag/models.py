"""Typed records for the internal knowledge base."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    supplier: str | None = None
    product: str | None = None
    region: str | None = None
    document_type: str
    confidentiality: str = "internal"
    valid_from: date | None = None
    valid_until: date | None = None
    source_date: date | None = None
    version: str | None = None
    source: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def is_valid(self, as_of: date) -> bool:
        return (self.valid_from is None or self.valid_from <= as_of) and (self.valid_until is None or as_of <= self.valid_until)


class EnterpriseDocument(BaseModel):
    document_id: str
    text: str
    metadata: DocumentMetadata


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    metadata: DocumentMetadata
    chunk_index: int


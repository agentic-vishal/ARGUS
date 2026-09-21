"""Deterministic paragraph-aware chunking."""

from argus.rag.cleaning import clean_text
from argus.rag.models import DocumentChunk, EnterpriseDocument


def chunk_document(document: EnterpriseDocument, chunk_size: int = 800, overlap: int = 120) -> list[DocumentChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be less than chunk_size")
    words = clean_text(document.text).split()
    chunks: list[DocumentChunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(DocumentChunk(
            chunk_id=f"{document.document_id}:chunk:{index}",
            document_id=document.document_id,
            text=" ".join(words[start:end]),
            metadata=document.metadata,
            chunk_index=index,
        ))
        if end == len(words):
            break
        start = end - overlap
        index += 1
    return chunks


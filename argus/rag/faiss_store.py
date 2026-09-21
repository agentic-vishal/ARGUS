"""FAISS vector index with metadata-aware retrieval."""

from datetime import UTC, date, datetime
from typing import Any

import faiss

from argus.models.schemas import Evidence
from argus.rag.embeddings import Embedder, HashEmbedder
from argus.rag.models import DocumentChunk


class FaissKnowledgeBase:
    def __init__(self, embedder: Embedder | None = None) -> None:
        self.embedder = embedder or HashEmbedder()
        self.index = faiss.IndexFlatIP(self.embedder.dimension)
        self.chunks: list[DocumentChunk] = []

    def add(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return
        vectors = self.embedder.encode([chunk.text for chunk in chunks]).astype("float32")
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query: str, *, filters: dict[str, Any] | None = None, limit: int = 10, as_of: date | None = None) -> list[Evidence]:
        if not self.chunks or limit <= 0:
            return []
        filters = filters or {}
        as_of = as_of or datetime.now(UTC).date()
        query_vector = self.embedder.encode([query]).astype("float32")
        scores, indices = self.index.search(query_vector, len(self.chunks))
        results: list[Evidence] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            chunk = self.chunks[int(index)]
            metadata = chunk.metadata
            if not metadata.is_valid(as_of):
                continue
            if any(
                (getattr(metadata, key, None) not in value if isinstance(value, (set, list, tuple)) else getattr(metadata, key, None) != value)
                for key, value in filters.items() if hasattr(metadata, key)
            ):
                continue
            results.append(Evidence(
                evidence_id=chunk.chunk_id,
                source_id=chunk.document_id,
                source_type=metadata.document_type,
                title=metadata.document_id,
                content=chunk.text,
                authority_score=1.0 if metadata.document_type in {"contract", "regulatory_guidance"} else 0.7,
                recency_score=recency_score(metadata, as_of),
                metadata={**metadata.model_dump(mode="json"), "similarity": float(score), "chunk_index": chunk.chunk_index},
            ))
        return rerank_results(results, as_of=as_of, limit=limit)


def recency_score(metadata: Any, as_of: date) -> float:
    if metadata.valid_until and metadata.valid_until < as_of:
        return 0.0
    if not metadata.source_date:
        return 0.5
    age = max(0, (as_of - metadata.source_date).days)
    return max(0.0, 1.0 - min(age, 3650) / 3650)


def rerank_results(results: list[Evidence], *, as_of: date, limit: int) -> list[Evidence]:
    def rank(item: Evidence) -> float:
        similarity = float(item.metadata.get("similarity", 0.0))
        validity = 1.0 if item.metadata.get("valid_until") is None or date.fromisoformat(item.metadata["valid_until"]) >= as_of else 0.0
        return (similarity * 0.55) + (item.authority_score * 0.25) + (item.recency_score * 0.15) + (validity * 0.05)
    return sorted(results, key=rank, reverse=True)[:limit]

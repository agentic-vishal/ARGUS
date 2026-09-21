"""Metadata-aware reranking helpers."""

from datetime import UTC, date, datetime

from argus.models.schemas import Evidence
from argus.rag.faiss_store import rerank_results


def rerank(results: list[Evidence], *, as_of: date | None = None, limit: int = 10) -> list[Evidence]:
    return rerank_results(results, as_of=as_of or datetime.now(UTC).date(), limit=limit)

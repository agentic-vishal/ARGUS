"""Provider-neutral retrieval interfaces."""

from datetime import date
from typing import Any, Protocol

from argus.models.schemas import Evidence


class Retriever(Protocol):
    def search(self, query: str, *, filters: dict[str, Any] | None = None, limit: int = 10, as_of: date | None = None) -> list[Evidence]: ...

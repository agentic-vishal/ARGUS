"""Checkpoint interface for durable graph execution."""

import json
from pathlib import Path
from typing import Protocol

from argus.graph.state import IntelligenceState


class Checkpointer(Protocol):
    def save(self, run_id: str, state: IntelligenceState) -> None: ...
    def load(self, run_id: str) -> IntelligenceState | None: ...


class JsonFileCheckpointer:
    """Simple durable checkpoint store for local runs."""

    def __init__(self, directory: str | Path = ".argus/checkpoints") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, run_id: str, state: IntelligenceState) -> None:
        target = self.directory / f"{run_id}.json"
        target.write_text(json.dumps(state, default=str, indent=2), encoding="utf-8")

    def load(self, run_id: str) -> IntelligenceState | None:
        target = self.directory / f"{run_id}.json"
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))

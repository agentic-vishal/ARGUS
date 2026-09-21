"""Structured audit events for reconstructing agent decisions."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def audit_event(event_type: str, **details: Any) -> dict[str, Any]:
    return {"timestamp": datetime.now(UTC).isoformat(), "event_type": event_type, **details}


class AuditLog:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.events: list[dict[str, Any]] = []

    def record(self, event_type: str, **details: Any) -> dict[str, Any]:
        event = audit_event(event_type, **details)
        self.events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, default=str) + "\n")
        return event

    def transition(self, from_node: str, to_node: str, **details: Any) -> dict[str, Any]:
        return self.record("graph_transition", from_node=from_node, to_node=to_node, **details)


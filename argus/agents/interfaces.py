"""Interfaces for specialist agents and the supervisor."""

from typing import Protocol

from argus.graph.state import IntelligenceState


class Agent(Protocol):
    name: str

    def run(self, state: IntelligenceState) -> dict: ...


class Supervisor(Protocol):
    def plan(self, state: IntelligenceState) -> list[str]: ...


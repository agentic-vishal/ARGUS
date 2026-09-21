"""Bounded investigation controls."""

from argus.config.settings import Settings
from argus.graph.state import IntelligenceState


class BudgetExceeded(RuntimeError):
    pass


class BudgetGuard:
    def __init__(self, *, max_tool_calls: int = 25, max_model_calls: int = 25, max_cost: float = 10.0) -> None:
        self.max_tool_calls, self.max_model_calls, self.max_cost = max_tool_calls, max_model_calls, max_cost
        self.tool_calls = self.model_calls = 0
        self.cost = 0.0

    def allow_tool(self) -> None:
        if self.tool_calls >= self.max_tool_calls:
            raise BudgetExceeded("tool-call budget exhausted")
        self.tool_calls += 1

    def allow_model(self, estimated_cost: float = 0.0) -> None:
        if self.model_calls >= self.max_model_calls or self.cost + estimated_cost > self.max_cost:
            raise BudgetExceeded("model or cost budget exhausted")
        self.model_calls += 1
        self.cost += estimated_cost


def budget_exhausted(state: IntelligenceState, settings: Settings) -> bool:
    return state.get("investigation_iterations", 0) >= settings.max_investigation_iterations

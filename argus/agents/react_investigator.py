"""Bounded, graph-controlled ReAct investigation controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from argus.graph.dependencies import WorkflowDependencies
from argus.graph.state import IntelligenceState
from argus.guardrails.audit import AuditLog

ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler


@dataclass
class ToolRegistry:
    tools: dict[str, ToolSpec] = field(default_factory=dict)
    allowlist: set[str] = field(default_factory=set)
    audit_log: AuditLog | None = None

    def register(self, name: str, description: str, handler: ToolHandler) -> None:
        self.tools[name] = ToolSpec(name, description, handler)

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.allowlist:
            raise PermissionError(f"Tool is not allowlisted: {name}")
        if name not in self.tools:
            raise KeyError(f"Tool is not registered: {name}")
        if self.audit_log:
            self.audit_log.record("tool_call", tool=name, arguments={key: str(value)[:120] for key, value in arguments.items()})
        result = self.tools[name].handler(arguments)
        if self.audit_log:
            self.audit_log.record("tool_result", tool=name, result_type=type(result).__name__)
        return result

    def available(self) -> list[str]:
        return sorted(set(self.tools) & self.allowlist)


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


def build_default_registry(deps: WorkflowDependencies, allowlist: set[str] | None = None) -> ToolRegistry:
    registry = ToolRegistry(audit_log=deps.audit_log, allowlist=allowlist if allowlist is not None else {
        "news.search_news", "news.search_company_news", "government.search_regulation",
        "government.get_notice", "government.search_trade_controls", "rag.search",
        "company.supplier_lookup", "company.company_profile", "company.get_company_events",
        "market.get_market_news",
    })
    registry.register("news.search_news", "Search current news", lambda a: deps.news.search_news(a["query"], a.get("date_range"), a.get("region")))
    registry.register("news.search_company_news", "Search news for a company", lambda a: deps.news.search_company_news(a["company"]))
    registry.register("government.search_regulation", "Search official regulations", lambda a: deps.government.search_regulation(a["query"], a.get("jurisdiction")))
    registry.register("government.get_notice", "Retrieve an official notice", lambda a: deps.government.get_notice(a["document_id"]))
    registry.register("government.search_trade_controls", "Search trade controls", lambda a: deps.government.search_trade_controls(a["product"], a["country"]))
    registry.register("rag.search", "Search internal enterprise knowledge", lambda a: deps.retriever.search(a["query"], filters=a.get("filters"), limit=a.get("limit", 10)))
    registry.register("company.supplier_lookup", "Look up supplier exposure", lambda a: deps.company.supplier_lookup(a["company"]) if hasattr(deps, "company") else {})
    registry.register("company.company_profile", "Look up company profile", lambda a: deps.company.company_profile(a["company"]) if hasattr(deps, "company") else {})
    registry.register("company.get_company_events", "Look up company events", lambda a: deps.company.get_company_events(a["company"]) if hasattr(deps, "company") else [])
    registry.register("market.get_market_news", "Search market news", lambda a: deps.market.get_market_news(a["symbol"]))
    return registry


@dataclass
class ReActInvestigator:
    registry: ToolRegistry
    max_iterations: int = 8
    max_tool_calls: int = 8

    def _candidates(self, state: IntelligenceState) -> list[tuple[float, str, dict[str, Any], str]]:
        objective = state.get("investigation_objective", state.get("user_query", ""))
        candidates: list[tuple[float, str, dict[str, Any], str]] = []
        if "rag.search" in self.registry.available() and not state.get("internal_documents"):
            candidates.append((0.95, "rag.search", {"query": objective, "limit": 10}, "Internal exposure is unknown."))
        if "government.search_regulation" in self.registry.available() and not state.get("government_sources"):
            candidates.append((0.90, "government.search_regulation", {"query": objective}, "Primary regulatory evidence is missing."))
        if "news.search_news" in self.registry.available() and not state.get("news_articles"):
            candidates.append((0.85, "news.search_news", {"query": objective}, "External event discovery is missing."))
        if state.get("conflicting_claims") and "government.search_regulation" in self.registry.available():
            candidates.append((1.0, "government.search_regulation", {"query": objective}, "Conflicting claims need primary verification."))
        companies = state.get("companies", []) or state.get("impacted_suppliers", [])
        if companies and "news.search_company_news" in self.registry.available():
            candidates.append((0.80, "news.search_company_news", {"company": companies[0]}, "Supplier-specific evidence is needed."))
        if companies and "company.supplier_lookup" in self.registry.available():
            candidates.append((0.78, "company.supplier_lookup", {"company": companies[0]}, "Supplier exposure needs validation."))
        return candidates

    def step(self, state: IntelligenceState) -> dict[str, Any]:
        iteration = state.get("react_iterations", 0)
        calls = state.get("react_tool_calls", 0)
        budget = state.get("research_budget_remaining", self.max_tool_calls)
        if iteration == 0 and calls == 0 and budget == 0:
            budget = self.max_tool_calls
        if iteration >= self.max_iterations or calls >= self.max_tool_calls or budget <= 0:
            return {"route": "budget_exit", "termination_reason": "ReAct research budget exhausted"}
        candidates = self._candidates(state)
        if not candidates:
            return {"route": "normal_completion", "termination_reason": "No useful allowlisted action remains"}
        _, tool_name, arguments, thought = max(candidates, key=lambda item: (item[0], item[1]))
        safe_args = {key: str(value)[:120] for key, value in arguments.items()}
        try:
            observation = _dump(self.registry.call(tool_name, arguments))
            success = True
            error = ""
        except Exception as exc:  # noqa: BLE001 - tool failures are recorded and isolated
            observation, success, error = {"error": type(exc).__name__}, False, str(exc)
        trace_entry = {
            "iteration": iteration + 1, "thought": thought, "action": tool_name,
            "arguments": safe_args, "observation": observation, "success": success,
        }
        update: dict[str, Any] = {
            "react_iterations": iteration + 1,
            "react_tool_calls": calls + 1,
            "research_budget_remaining": budget - 1,
            "react_trace": [*state.get("react_trace", []), trace_entry],
            "last_action": tool_name,
            "last_observation": observation if isinstance(observation, dict) else {"items": observation},
            "next_action": "",
            "route": "continue",
        }
        if error:
            update["tool_errors"] = [*state.get("tool_errors", []), error]
        target = {
            "rag.search": "internal_documents", "news.search_news": "news_articles",
            "government.search_regulation": "government_sources", "news.search_company_news": "news_articles",
            "market.get_market_news": "market_signals",
        }.get(tool_name)
        if target:
            update[target] = observation if isinstance(observation, list) else [observation]
        return update

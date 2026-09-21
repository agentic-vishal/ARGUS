"""Three-tier model cascade with configurable routing and telemetry."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol

TIERS = ("tier_1", "tier_2", "tier_3")


@dataclass(frozen=True)
class ModelRequest:
    task: str
    prompt: str
    complexity: float = 0.5
    confidence: float | None = None
    material: bool = False
    max_tokens: int = 512
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TierConfig:
    name: str
    model_name: str
    input_cost_per_1k: float
    output_cost_per_1k: float


@dataclass(frozen=True)
class RoutingRule:
    task: str
    tier: str
    min_complexity: float = 0.0
    material_only: bool = False


@dataclass
class ModelResult:
    output: str
    tier: str
    model_name: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    fallback_used: bool = False
    fallback_reason: str | None = None


@dataclass
class CascadeTelemetry:
    calls: list[ModelResult] = field(default_factory=list)

    def record(self, result: ModelResult) -> None:
        self.calls.append(result)

    def summary(self) -> dict[str, Any]:
        return {
            "call_count": len(self.calls),
            "total_latency_ms": round(sum(item.latency_ms for item in self.calls), 2),
            "total_input_tokens": sum(item.input_tokens for item in self.calls),
            "total_output_tokens": sum(item.output_tokens for item in self.calls),
            "total_estimated_cost": round(sum(item.estimated_cost for item in self.calls), 8),
            "tiers": {tier: sum(item.tier == tier for item in self.calls) for tier in TIERS},
        }


class ModelHandler(Protocol):
    def complete(self, request: ModelRequest) -> str: ...


class TieredModelRouter:
    """Routes work to the least expensive suitable tier and falls back upward."""

    DEFAULT_RULES = (
        RoutingRule("relevance", "tier_1"), RoutingRule("language_detection", "tier_1"),
        RoutingRule("topic_detection", "tier_1"), RoutingRule("entity_extraction", "tier_1"),
        RoutingRule("duplicate_filtering", "tier_1"), RoutingRule("structured_summary", "tier_2"),
        RoutingRule("claim_extraction", "tier_2"), RoutingRule("preliminary_risk", "tier_2"),
        RoutingRule("contradiction_candidates", "tier_2"), RoutingRule("cross_source_reasoning", "tier_3"),
        RoutingRule("business_exposure", "tier_3"), RoutingRule("scenario_analysis", "tier_3"),
        RoutingRule("recommendation", "tier_3"),
    )

    def __init__(self, handlers: dict[str, ModelHandler] | None = None, *, tier_configs: dict[str, TierConfig] | None = None, rules: tuple[RoutingRule, ...] | None = None, telemetry: CascadeTelemetry | None = None, max_fallbacks: int = 2, audit_log: Any | None = None) -> None:
        self.handlers = handlers or {}
        self.tier_configs = tier_configs or {
            "tier_1": TierConfig("tier_1", "small-fast", 0.0002, 0.0006),
            "tier_2": TierConfig("tier_2", "mid-tier", 0.001, 0.003),
            "tier_3": TierConfig("tier_3", "strong-reasoning", 0.005, 0.015),
        }
        self.rules = rules or self.DEFAULT_RULES
        self.telemetry = telemetry or CascadeTelemetry()
        self.max_fallbacks = max_fallbacks
        self.audit_log = audit_log

    def tier_for(self, request: ModelRequest) -> str:
        matches = [rule for rule in self.rules if rule.task == request.task and (not rule.material_only or request.material) and request.complexity >= rule.min_complexity]
        selected = matches[-1].tier if matches else ("tier_3" if request.complexity >= 0.7 or request.material else "tier_1")
        if request.confidence is not None and request.confidence < 0.6:
            selected = self.escalate(selected)
        return selected

    @staticmethod
    def escalate(tier: str) -> str:
        return TIERS[min(TIERS.index(tier) + 1, len(TIERS) - 1)]

    @staticmethod
    def _tokens(text: str) -> int:
        return max(1, len(text.split()))

    def run(self, request: ModelRequest) -> ModelResult:
        selected = self.tier_for(request)
        fallback_reason: str | None = None
        for attempt in range(self.max_fallbacks + 1):
            tier = TIERS[min(TIERS.index(selected) + attempt, len(TIERS) - 1)]
            handler = self.handlers.get(tier)
            if handler is None:
                fallback_reason = f"handler unavailable for {tier}"
                continue
            started = time.perf_counter()
            try:
                output = handler.complete(request)
                latency_ms = (time.perf_counter() - started) * 1000
                config = self.tier_configs[tier]
                input_tokens = self._tokens(request.prompt)
                output_tokens = self._tokens(output)
                result = ModelResult(
                    output=output, tier=tier, model_name=config.model_name,
                    latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens,
                    estimated_cost=(input_tokens / 1000 * config.input_cost_per_1k) + (output_tokens / 1000 * config.output_cost_per_1k),
                    fallback_used=attempt > 0, fallback_reason=fallback_reason,
                )
                self.telemetry.record(result)
                if self.audit_log:
                    self.audit_log.record("model_call", task=request.task, tier=tier, model=config.model_name, latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost=result.estimated_cost, fallback_used=attempt > 0)
                return result
            except Exception as exc:  # noqa: BLE001 - cascade must continue to fallback tiers
                fallback_reason = f"{tier} failed: {type(exc).__name__}"
        raise RuntimeError(f"No model tier completed request: {fallback_reason}")

    def complete(self, request: ModelRequest, **kwargs: Any) -> str:
        return self.run(request).output

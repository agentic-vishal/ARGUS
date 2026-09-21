"""Dependency container used to keep graph nodes pure and replaceable."""

from dataclasses import dataclass, field
from typing import Any

from argus.config.settings import Settings
from argus.guardrails.access_control import AccessPolicy
from argus.guardrails.audit import AuditLog
from argus.mcp.interfaces import CompanyClient, GovernmentClient, MarketClient, NewsClient
from argus.models.cascade import TieredModelRouter
from argus.rag.interfaces import Retriever


class EmptyNewsClient:
    def search_news(self, query: str, date_range: str | None = None, region: str | None = None) -> list[dict[str, Any]]:
        return []

    def get_article(self, article_id: str) -> dict[str, Any]:
        return {}

    def search_company_news(self, company: str) -> list[dict[str, Any]]:
        return []


class EmptyGovernmentClient:
    def search_regulation(self, query: str, jurisdiction: str | None = None) -> list[dict[str, Any]]:
        return []

    def get_notice(self, document_id: str) -> dict[str, Any]:
        return {}

    def search_trade_controls(self, product: str, country: str) -> list[dict[str, Any]]:
        return []


class EmptyMarketClient:
    def get_stock_price(self, symbol: str) -> float:
        return 0.0

    def get_fx_rate(self, pair: str) -> float:
        return 0.0

    def get_commodity_price(self, symbol: str) -> float:
        return 0.0

    def get_market_news(self, symbol: str) -> list[dict[str, Any]]:
        return []


class EmptyCompanyClient:
    def company_profile(self, company: str) -> dict[str, Any]:
        return {}

    def supplier_lookup(self, company: str) -> dict[str, Any]:
        return {}

    def get_company_events(self, company: str) -> list[dict[str, Any]]:
        return []


class EmptyRetriever:
    def search(self, query: str, *, filters: dict[str, Any] | None = None, limit: int = 10, as_of: Any = None) -> list[Any]:
        return []


@dataclass
class WorkflowDependencies:
    settings: Settings = field(default_factory=Settings)
    news: NewsClient = field(default_factory=EmptyNewsClient)
    government: GovernmentClient = field(default_factory=EmptyGovernmentClient)
    market: MarketClient = field(default_factory=EmptyMarketClient)
    company: CompanyClient = field(default_factory=EmptyCompanyClient)
    retriever: Retriever = field(default_factory=EmptyRetriever)
    model_router: TieredModelRouter = field(default_factory=TieredModelRouter)
    audit_log: AuditLog = field(default_factory=AuditLog)
    access_policy: AccessPolicy = field(default_factory=AccessPolicy)

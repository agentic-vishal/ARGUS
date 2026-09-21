"""HTTP MCP client implementations and deterministic local mock adapters."""

from typing import Any

from argus.config.settings import Settings
from argus.mcp.schemas import (
    CompanyEvent,
    CompanyProfile,
    MarketQuote,
    NewsArticle,
    RegulationNotice,
    SupplierRecord,
    TradeControl,
)
from argus.mcp.transport import HTTPMCPTransport


def _items(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return response
    return response.get("items", response.get("results", [])) if isinstance(response, dict) else []


class HTTPNewsClient:
    def __init__(self, transport: HTTPMCPTransport, base_url: str) -> None:
        self.transport, self.base_url = transport, base_url

    def search_news(self, query: str, date_range: str | None = None, region: str | None = None) -> list[NewsArticle]:
        data = self.transport.request(self.base_url, "GET", "/search_news", params={"query": query, "date_range": date_range, "region": region})
        return [NewsArticle.model_validate(item) for item in _items(data)]

    def get_article(self, article_id: str) -> NewsArticle:
        return NewsArticle.model_validate(self.transport.request(self.base_url, "GET", f"/articles/{article_id}"))

    def search_company_news(self, company: str) -> list[NewsArticle]:
        data = self.transport.request(self.base_url, "GET", "/company_news", params={"company": company})
        return [NewsArticle.model_validate(item) for item in _items(data)]


class HTTPGovernmentClient:
    def __init__(self, transport: HTTPMCPTransport, base_url: str) -> None:
        self.transport, self.base_url = transport, base_url

    def search_regulation(self, query: str, jurisdiction: str | None = None) -> list[RegulationNotice]:
        data = self.transport.request(self.base_url, "GET", "/search_regulation", params={"query": query, "jurisdiction": jurisdiction})
        return [RegulationNotice.model_validate(item) for item in _items(data)]

    def get_notice(self, document_id: str) -> RegulationNotice:
        return RegulationNotice.model_validate(self.transport.request(self.base_url, "GET", f"/notices/{document_id}"))

    def search_trade_controls(self, product: str, country: str) -> list[TradeControl]:
        data = self.transport.request(self.base_url, "GET", "/search_trade_controls", params={"product": product, "country": country})
        return [TradeControl.model_validate(item) for item in _items(data)]


class HTTPMarketClient:
    def __init__(self, transport: HTTPMCPTransport, base_url: str) -> None:
        self.transport, self.base_url = transport, base_url

    def get_stock_price(self, symbol: str) -> MarketQuote:
        return MarketQuote.model_validate(self.transport.request(self.base_url, "GET", "/stock_price", params={"symbol": symbol}))

    def get_fx_rate(self, pair: str) -> MarketQuote:
        return MarketQuote.model_validate(self.transport.request(self.base_url, "GET", "/fx_rate", params={"pair": pair}))

    def get_commodity_price(self, symbol: str) -> MarketQuote:
        return MarketQuote.model_validate(self.transport.request(self.base_url, "GET", "/commodity_price", params={"symbol": symbol}))

    def get_market_news(self, symbol: str) -> list[NewsArticle]:
        data = self.transport.request(self.base_url, "GET", "/market_news", params={"symbol": symbol})
        return [NewsArticle.model_validate(item) for item in _items(data)]


class HTTPCompanyClient:
    def __init__(self, transport: HTTPMCPTransport, base_url: str) -> None:
        self.transport, self.base_url = transport, base_url

    def company_profile(self, company: str) -> CompanyProfile:
        return CompanyProfile.model_validate(self.transport.request(self.base_url, "GET", "/company_profile", params={"company": company}))

    def supplier_lookup(self, company: str) -> SupplierRecord:
        return SupplierRecord.model_validate(self.transport.request(self.base_url, "GET", "/supplier_lookup", params={"company": company}))

    def get_company_events(self, company: str) -> list[CompanyEvent]:
        data = self.transport.request(self.base_url, "GET", "/company_events", params={"company": company})
        return [CompanyEvent.model_validate(item) for item in _items(data)]


class MockMCPClients:
    """Deterministic adapters for local development and tests."""

    def search_news(self, query: str, date_range: str | None = None, region: str | None = None) -> list[NewsArticle]:
        return [NewsArticle(article_id="mock-news-1", title=f"Mock report: {query}", summary="Synthetic local evidence", source="mock", region=region)]

    def get_article(self, article_id: str) -> NewsArticle:
        return NewsArticle(article_id=article_id, title="Mock article", summary="Synthetic local article", source="mock")

    def search_company_news(self, company: str) -> list[NewsArticle]:
        return [NewsArticle(article_id="mock-company-news-1", title=f"Mock update for {company}", source="mock", companies=[company])]

    def search_regulation(self, query: str, jurisdiction: str | None = None) -> list[RegulationNotice]:
        return [RegulationNotice(document_id="mock-notice-1", title=f"Mock notice: {query}", jurisdiction=jurisdiction, summary="Synthetic local regulation")]

    def get_notice(self, document_id: str) -> RegulationNotice:
        return RegulationNotice(document_id=document_id, title="Mock regulatory notice", summary="Synthetic local notice")

    def search_trade_controls(self, product: str, country: str) -> list[TradeControl]:
        return [TradeControl(control_id="mock-control-1", product=product, country=country, status="under_review")]

    def get_stock_price(self, symbol: str) -> MarketQuote:
        return MarketQuote(symbol=symbol, value=100.0, currency="USD")

    def get_fx_rate(self, pair: str) -> MarketQuote:
        return MarketQuote(symbol=pair, value=1.0, currency=pair[-3:])

    def get_commodity_price(self, symbol: str) -> MarketQuote:
        return MarketQuote(symbol=symbol, value=75.0, currency="USD")

    def get_market_news(self, symbol: str) -> list[NewsArticle]:
        return [NewsArticle(article_id="mock-market-news-1", title=f"Mock market news for {symbol}", source="mock")]

    def company_profile(self, company: str) -> CompanyProfile:
        return CompanyProfile(company_id=f"mock-{company.lower().replace(' ', '-')}", name=company, industry="technology")

    def supplier_lookup(self, company: str) -> SupplierRecord:
        return SupplierRecord(supplier_id=f"mock-{company.lower().replace(' ', '-')}", name=company, status="active")

    def get_company_events(self, company: str) -> list[CompanyEvent]:
        return [CompanyEvent(event_id="mock-event-1", company=company, event_type="update", title="Mock company update")]


def build_http_clients(settings: Settings) -> dict[str, Any]:
    transport = HTTPMCPTransport(settings)
    clients: dict[str, Any] = {}
    if settings.news_mcp_url:
        clients["news"] = HTTPNewsClient(transport, settings.news_mcp_url)
    if settings.government_mcp_url:
        clients["government"] = HTTPGovernmentClient(transport, settings.government_mcp_url)
    if settings.market_mcp_url:
        clients["market"] = HTTPMarketClient(transport, settings.market_mcp_url)
    if settings.company_mcp_url:
        clients["company"] = HTTPCompanyClient(transport, settings.company_mcp_url)
    return clients

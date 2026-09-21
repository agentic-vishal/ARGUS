"""Typed MCP request and response records."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    article_id: str
    title: str
    summary: str = ""
    url: str | None = None
    source: str | None = None
    published_at: datetime | None = None
    region: str | None = None
    companies: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RegulationNotice(BaseModel):
    document_id: str
    title: str
    summary: str = ""
    jurisdiction: str | None = None
    effective_date: date | None = None
    source_url: str | None = None
    products: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class TradeControl(BaseModel):
    control_id: str
    product: str
    country: str
    status: str
    effective_date: date | None = None
    source_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class MarketQuote(BaseModel):
    symbol: str
    value: float
    currency: str | None = None
    as_of: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CompanyProfile(BaseModel):
    company_id: str
    name: str
    country: str | None = None
    industry: str | None = None
    website: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class SupplierRecord(BaseModel):
    supplier_id: str
    name: str
    products: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    status: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CompanyEvent(BaseModel):
    event_id: str
    company: str
    event_type: str
    title: str
    event_date: date | None = None
    summary: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


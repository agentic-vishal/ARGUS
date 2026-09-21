"""Small HTTP transport shared by MCP adapters."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from argus.config.settings import Settings

logger = logging.getLogger(__name__)


class MCPTransportError(RuntimeError):
    """Raised after a request exhausts its bounded retry policy."""


def _safe(value: Any) -> str:
    text = str(value).replace("\n", " ")
    for secret in ("token", "api_key", "authorization", "password"):
        text = text.replace(secret, "[redacted]")
    return text[:160]


@dataclass
class HTTPMCPTransport:
    settings: Settings

    def request(self, base_url: str, method: str, path: str = "", *, params: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> Any:
        if not base_url:
            raise MCPTransportError(f"No MCP endpoint configured for {method}")
        query = f"?{urlencode({k: v for k, v in (params or {}).items() if v is not None})}" if params else ""
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if path else base_url.rstrip('/')
        url = url + query
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=body, method=method.upper(), headers={"Content-Type": "application/json", "Accept": "application/json"})
        attempts = self.settings.mcp_max_retries + 1
        for attempt in range(attempts):
            logger.info("mcp_request", extra={"method": method, "endpoint": _safe(path), "attempt": attempt + 1})
            try:
                with urlopen(request, timeout=self.settings.mcp_timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                retryable = exc.code == 429 or exc.code >= 500
                error = f"HTTP {exc.code} from {_safe(path)}"
            except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                retryable, error = True, f"{type(exc).__name__} from {_safe(path)}"
            if not retryable or attempt == attempts - 1:
                raise MCPTransportError(error) from None
            delay = self.settings.mcp_retry_backoff_seconds * (2**attempt)
            logger.warning("mcp_retry", extra={"endpoint": _safe(path), "delay_seconds": delay})
            time.sleep(delay)
        raise MCPTransportError("MCP request failed")


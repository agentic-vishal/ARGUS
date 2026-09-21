import unittest

from argus.config.settings import Settings
from argus.mcp.clients import HTTPGovernmentClient, HTTPNewsClient, MockMCPClients
from argus.mcp.schemas import NewsArticle, RegulationNotice
from argus.mcp.transport import HTTPMCPTransport, MCPTransportError


class FakeTransport:
    def request(self, base_url, method, path="", *, params=None, payload=None):
        if path == "/search_news":
            return {"items": [{"article_id": "a1", "title": "Export control update"}]}
        if path == "/search_regulation":
            return {"results": [{"document_id": "r1", "title": "Official notice"}]}
        raise AssertionError(path)


class McpTests(unittest.TestCase):
    def test_mock_adapters_return_typed_records(self) -> None:
        client = MockMCPClients()
        self.assertIsInstance(client.search_news("semiconductors")[0], NewsArticle)
        self.assertIsInstance(client.search_regulation("export controls")[0], RegulationNotice)
        self.assertEqual(client.get_stock_price("ABC").value, 100.0)
        self.assertEqual(client.supplier_lookup("Supplier ABC").status, "active")

    def test_http_clients_normalize_payloads(self) -> None:
        news = HTTPNewsClient(FakeTransport(), "http://news")
        government = HTTPGovernmentClient(FakeTransport(), "http://government")
        self.assertEqual(news.search_news("query")[0].article_id, "a1")
        self.assertEqual(government.search_regulation("query")[0].document_id, "r1")

    def test_transport_requires_endpoint(self) -> None:
        with self.assertRaises(MCPTransportError):
            HTTPMCPTransport(Settings()).request("", "GET", "/test")


if __name__ == "__main__":
    unittest.main()

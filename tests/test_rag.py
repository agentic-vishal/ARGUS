import unittest
from datetime import date

from argus.rag.chunking import chunk_document
from argus.rag.enrichment import enrich_metadata
from argus.rag.faiss_store import FaissKnowledgeBase
from argus.rag.ingest import normalize_document


class RagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kb = FaissKnowledgeBase()
        active = normalize_document(
            "Supplier ABC provides GPU accelerators for Product Alpha and maintains 45 days of safety stock.",
            {"supplier": "Supplier ABC", "product": "Product Alpha", "region": "China", "document_type": "contract", "confidentiality": "restricted", "valid_until": "2026-12-31", "source_date": "2026-01-10"},
            document_id="active-contract",
        )
        expired = normalize_document(
            "Supplier ABC provides GPU accelerators for Product Alpha with only 15 days of safety stock.",
            {"supplier": "Supplier ABC", "product": "Product Alpha", "region": "China", "document_type": "contract", "confidentiality": "restricted", "valid_until": "2024-12-31", "source_date": "2024-01-10"},
            document_id="expired-contract",
        )
        self.kb.add(chunk_document(active) + chunk_document(expired))

    def test_metadata_is_normalized(self) -> None:
        metadata = enrich_metadata("doc-1", {"document_type": "contract", "valid_until": "2026-12-31", "owner": "procurement"})
        self.assertEqual(metadata.valid_until, date(2026, 12, 31))
        self.assertEqual(metadata.extra["owner"], "procurement")

    def test_expired_document_is_excluded(self) -> None:
        results = self.kb.search("GPU accelerator safety stock", as_of=date(2026, 9, 20))
        self.assertTrue(results)
        self.assertTrue(all(result.source_id == "active-contract" for result in results))

    def test_metadata_filters_limit_results(self) -> None:
        results = self.kb.search("GPU accelerator", filters={"supplier": "Supplier ABC", "region": "China"}, as_of=date(2026, 9, 20))
        self.assertTrue(results)
        self.assertTrue(all(result.metadata["supplier"] == "Supplier ABC" for result in results))

    def test_chunking_produces_stable_ids(self) -> None:
        document = normalize_document("one two three four five", {"document_type": "memo"}, document_id="memo-1")
        chunks = chunk_document(document, chunk_size=3, overlap=1)
        self.assertEqual([chunk.chunk_id for chunk in chunks], ["memo-1:chunk:0", "memo-1:chunk:1"])


if __name__ == "__main__":
    unittest.main()

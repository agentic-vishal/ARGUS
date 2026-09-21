import unittest

from argus.graph.dependencies import WorkflowDependencies
from argus.graph.nodes import claim_extraction_node, contradiction_detection_node, verification_node
from argus.models.schemas import Claim


class EvidenceHandlingTests(unittest.TestCase):
    def test_claim_extraction_preserves_provenance(self) -> None:
        state = {"government_sources": [{
            "document_id": "gov-1", "title": "Official notice", "summary": "Effective September 1",
            "effective_date": "2026-09-01", "authority_score": 1.0,
        }]}
        update = claim_extraction_node(state, WorkflowDependencies())
        claim = Claim.model_validate(update["claims"][0])
        self.assertEqual(claim.provenance[0].source_id, "gov-1")
        self.assertTrue(claim.provenance[0].is_primary)
        self.assertEqual(claim.attributes["effective_date"], "2026-09-01")

    def test_primary_regulatory_source_gets_preferred_authority(self) -> None:
        state = {"claims": [
            {"claim_id": "news-1", "claim": "Restriction begins September 1", "claim_type": "effective_date", "sources": ["news-1"], "source_authority": 0.4, "recency_score": 0.9, "provenance": [{"source_id": "news-1", "source_type": "news", "is_primary": False, "authority_score": 0.4}]},
            {"claim_id": "gov-1", "claim": "Restriction begins September 1", "claim_type": "effective_date", "sources": ["gov-1"], "source_authority": 0.7, "recency_score": 0.8, "provenance": [{"source_id": "gov-1", "source_type": "government", "is_primary": True, "authority_score": 0.7}]},
        ]}
        update = verification_node(state, WorkflowDependencies())
        government = next(item for item in update["verified_claims"] if item["claim_id"] == "gov-1")
        self.assertEqual(government["source_authority"], 1.0)
        self.assertNotIn("authoritative primary source for regulatory facts", update["missing_information"])

    def test_date_and_scope_disagreements_remain_unresolved(self) -> None:
        state = {"verified_claims": [
            {"claim_id": "a", "claim": "Restriction covers GPUs", "claim_type": "restriction", "attributes": {"effective_date": "2026-09-01", "scope": "advanced GPUs"}, "sources": ["a"]},
            {"claim_id": "b", "claim": "Restriction covers GPUs", "claim_type": "restriction", "attributes": {"effective_date": "2026-10-01", "scope": "all GPUs"}, "sources": ["b"]},
        ]}
        update = contradiction_detection_node(state, WorkflowDependencies())
        claim = next(item for item in update["verified_claims"] if item["claim_id"] == "a")
        self.assertEqual(set(claim["contradiction_types"]), {"date", "scope"})
        self.assertEqual(claim["contradiction_status"], "unresolved")
        self.assertTrue(any("resolve date, scope" in item for item in update["missing_information"]))


if __name__ == "__main__":
    unittest.main()

import unittest

from argus.analysis.exposure import analyze_exposure
from argus.analysis.recommendations import generate_recommendations
from argus.analysis.risk import score_risk


class ExposureRiskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = {
            "verified_claims": [{"claim_id": "c1", "claim": "Supplier ABC GPU restriction", "claim_type": "scope", "sources": ["gov-1"], "attributes": {"products": ["GPU"]}}],
            "internal_documents": [{"document_id": "contract-1", "supplier": "Supplier ABC", "product": "GPU", "region": "China", "contract": "contract-1", "obligations": ["maintain 45 days inventory"], "text": "Supplier ABC provides GPU components."}],
            "confidence_score": 0.82,
            "conflicting_claims": [],
        }

    def test_exposure_retains_claim_and_document_references(self) -> None:
        matches = analyze_exposure(self.state)
        self.assertTrue(matches)
        self.assertIn("c1", matches[0]["evidence_refs"])
        self.assertEqual(matches[0]["contract"], "contract-1")

    def test_risk_dimensions_are_separate_and_transparent(self) -> None:
        state = {**self.state, "exposure_matches": analyze_exposure(self.state)}
        risk = score_risk(state)
        self.assertEqual(risk["confidence"], 0.82)
        self.assertIn("0.40*impact", risk["formula"])
        self.assertGreater(risk["impact"], 0)

    def test_recommendations_are_data_only(self) -> None:
        state = {**self.state, "exposure_matches": analyze_exposure(self.state), "risk_assessment": {"evidence_refs": ["gov-1", "contract-1"]}}
        actions = generate_recommendations(state)
        self.assertEqual(actions[0]["owner"], "procurement")
        self.assertEqual(actions[0]["evidence_refs"], ["gov-1", "contract-1"])
        self.assertFalse(any("execute" in key.lower() for action in actions for key in action))


if __name__ == "__main__":
    unittest.main()

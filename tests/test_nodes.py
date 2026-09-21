import unittest

from argus.graph.dependencies import WorkflowDependencies
from argus.graph.nodes import (
    contradiction_detection_node,
    final_report_node,
    risk_assessment_node,
    verification_node,
)


class NodeTests(unittest.TestCase):
    def test_verification_calculates_confidence(self) -> None:
        state = {"claims": [{
            "claim_id": "c1", "claim": "Restriction begins September 1", "claim_type": "effective_date",
            "sources": ["gov-1"], "source_authority": 1.0, "recency_score": 1.0,
        }]}
        update = verification_node(state, WorkflowDependencies())
        self.assertGreater(update["confidence_score"], 0.5)

    def test_contradictions_are_grouped_by_claim_type(self) -> None:
        state = {"verified_claims": [
            {"claim_type": "effective_date", "claim": "starts September 1"},
            {"claim_type": "effective_date", "claim": "starts immediately"},
        ]}
        update = contradiction_detection_node(state, WorkflowDependencies())
        self.assertEqual(len(update["conflicting_claims"]), 1)

    def test_final_report_is_generated(self) -> None:
        state = {"user_query": "Assess supplier exposure", "risk_assessment": {"risk_score": 7.2}, "confidence_score": 0.8}
        report = final_report_node(state, WorkflowDependencies())["final_report"]
        self.assertIn("ARGUS GLOBAL RISK INTELLIGENCE REPORT", report)

    def test_risk_assessment_is_bounded(self) -> None:
        state = {"verified_claims": [{"claim": "x"}], "impacted_products": ["A"], "impacted_suppliers": ["B"]}
        update = risk_assessment_node(state, WorkflowDependencies())
        self.assertLessEqual(update["risk_score"], 10.0)


if __name__ == "__main__":
    unittest.main()

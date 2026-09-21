import unittest

from argus.evaluation.scenarios import SCENARIOS
from argus.graph.dependencies import WorkflowDependencies
from argus.graph.nodes import (
    claim_extraction_node,
    contradiction_detection_node,
    evaluation_node,
    exposure_analysis_node,
    external_discovery_node,
    final_report_node,
    internal_retrieval_node,
    query_analysis_node,
    recommendation_node,
    risk_assessment_node,
    supervisor_node,
    verification_node,
)
from argus.mcp.clients import MockMCPClients


class FakeRetriever:
    def search(self, query, *, filters=None, limit=10, as_of=None):
        return [{"document_id": "contract-1", "supplier": "Supplier ABC", "product": "GPU", "region": "China", "contract": "contract-1", "obligations": ["maintain inventory"], "content": "Supplier ABC provides GPU components."}]


class EndToEndTests(unittest.TestCase):
    def test_mock_investigation_produces_sectioned_report(self) -> None:
        mock = MockMCPClients()
        deps = WorkflowDependencies(news=mock, government=mock, company=mock, retriever=FakeRetriever())
        state = {"user_query": "Assess semiconductor export restrictions affecting Supplier ABC", "investigation_iterations": 0, "missing_information": [], "tool_errors": [], "conflicting_claims": []}
        for node in (query_analysis_node, supervisor_node, external_discovery_node, internal_retrieval_node, claim_extraction_node, verification_node, contradiction_detection_node, exposure_analysis_node, risk_assessment_node, recommendation_node):
            state.update(node(state, deps))
        state.update(evaluation_node(state, deps))
        state.update(final_report_node(state, deps))
        for section in ("FACTS", "INFERENCE / BUSINESS EXPOSURE", "RISK", "CONFIDENCE", "EVIDENCE", "UNCERTAINTY", "UNRESOLVED CONFLICTS", "RECOMMENDED ACTIONS"):
            self.assertIn(section, state["final_report"])
        self.assertTrue(state["recommended_actions"])
        self.assertGreaterEqual(state["risk_score"], 0)

    def test_benchmark_catalog_is_complete(self) -> None:
        names = {scenario.name for scenario in SCENARIOS}
        self.assertEqual(len(names), 8)
        self.assertIn("prompt_injection", names)
        self.assertIn("cost_pressure", names)


if __name__ == "__main__":
    unittest.main()

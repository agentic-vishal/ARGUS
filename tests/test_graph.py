import unittest

from argus.agents.react_investigator import ReActInvestigator, ToolRegistry
from argus.graph.dependencies import WorkflowDependencies
from argus.graph.graph import InvestigationGraph
from argus.graph.nodes import evidence_sufficiency_node, query_analysis_node


class GraphTests(unittest.TestCase):
    def test_nodes_return_partial_state_updates(self) -> None:
        graph = InvestigationGraph(nodes=[lambda state: {"investigation_iterations": 1}])
        state = graph.run("Test query")
        self.assertEqual(state["investigation_iterations"], 1)

    def test_query_analysis_is_independently_testable(self) -> None:
        state = {"user_query": "Assess China semiconductor restrictions"}
        update = query_analysis_node(state, WorkflowDependencies())
        self.assertEqual(update["investigation_objective"], state["user_query"])
        self.assertIn("semiconductor", update["entities"])

    def test_budget_exit_is_selected(self) -> None:
        deps = WorkflowDependencies()
        state = {"investigation_iterations": deps.settings.max_investigation_iterations}
        self.assertEqual(evidence_sufficiency_node(state, deps)["route"], "budget_exit")

    def test_investigation_graph_reaches_final_report(self) -> None:
        state = InvestigationGraph().run("Investigate semiconductor export restrictions")
        self.assertTrue(state["final_report"])
        self.assertIn("ARGUS GLOBAL RISK INTELLIGENCE REPORT", state["final_report"])

    def test_react_respects_allowlist_and_budget(self) -> None:
        registry = ToolRegistry(allowlist={"rag.search"})
        registry.register("rag.search", "test", lambda args: [{"content": "evidence"}])
        investigator = ReActInvestigator(registry, max_iterations=1, max_tool_calls=1)
        state = {"user_query": "test", "investigation_objective": "test"}
        update = investigator.step(state)
        self.assertEqual(update["last_action"], "rag.search")
        self.assertEqual(update["route"], "continue")
        exhausted = {**state, **update}
        self.assertEqual(investigator.step(exhausted)["route"], "budget_exit")


if __name__ == "__main__":
    unittest.main()

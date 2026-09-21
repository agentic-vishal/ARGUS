"""LangGraph assembly for the ARGUS investigation lifecycle."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from argus.agents.react_investigator import ReActInvestigator, build_default_registry
from argus.graph.dependencies import WorkflowDependencies
from argus.graph.nodes import (
    claim_extraction_node,
    contradiction_detection_node,
    evaluation_node,
    evidence_sufficiency_node,
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
from argus.graph.state import IntelligenceState, initial_state

Node = Callable[[IntelligenceState], dict[str, Any]]


def _invoke_node(name: str, node: Callable, state: IntelligenceState, dependencies: WorkflowDependencies) -> dict[str, Any]:
    before = {"risk_score": state.get("risk_score", 0.0), "confidence_score": state.get("confidence_score", 0.0)}
    update = node(state, dependencies)
    after = {"risk_score": update.get("risk_score", before["risk_score"]), "confidence_score": update.get("confidence_score", before["confidence_score"])}
    event = dependencies.audit_log.record("graph_node", node=name, before_scores=before, after_scores=after)
    return {**update, "audit_events": [*state.get("audit_events", []), event]}


def _route_after_evidence(state: IntelligenceState) -> str:
    return state.get("route", "budget_exit")


def _route_after_evaluation(state: IntelligenceState) -> str:
    return state.get("route", "normal_completion")


def build_langgraph(deps: WorkflowDependencies | None = None):
    """Build and compile the conditional LangGraph workflow."""
    from langgraph.graph import END, START, StateGraph

    dependencies = deps or WorkflowDependencies()
    graph = StateGraph(IntelligenceState)
    node_specs = {
        "query_analysis": query_analysis_node,
        "supervisor": supervisor_node,
        "external_discovery": external_discovery_node,
        "internal_retrieval": internal_retrieval_node,
        "claim_extraction": claim_extraction_node,
        "verification": verification_node,
        "contradiction_detection": contradiction_detection_node,
        "evidence_sufficiency": evidence_sufficiency_node,
        "exposure_analysis": exposure_analysis_node,
        "risk_assessment": risk_assessment_node,
        "recommendation": recommendation_node,
        "evaluation": evaluation_node,
        "final_report": final_report_node,
    }
    for name, node in node_specs.items():
        graph.add_node(name, lambda state, node=node, name=name: _invoke_node(name, node, state, dependencies))

    graph.add_edge(START, "query_analysis")
    graph.add_edge("query_analysis", "supervisor")
    graph.add_edge("supervisor", "external_discovery")
    graph.add_edge("external_discovery", "internal_retrieval")
    graph.add_edge("internal_retrieval", "claim_extraction")
    graph.add_edge("claim_extraction", "verification")
    graph.add_edge("verification", "contradiction_detection")
    graph.add_edge("contradiction_detection", "evidence_sufficiency")
    graph.add_conditional_edges(
        "evidence_sufficiency", _route_after_evidence,
        {"retry": "external_discovery", "budget_exit": "risk_assessment", "normal_completion": "exposure_analysis"},
    )
    graph.add_edge("exposure_analysis", "risk_assessment")
    graph.add_edge("risk_assessment", "recommendation")
    graph.add_edge("recommendation", "evaluation")
    graph.add_conditional_edges(
        "evaluation", _route_after_evaluation,
        {"retry": "verification", "budget_exit": "final_report", "normal_completion": "final_report"},
    )
    graph.add_edge("final_report", END)
    return graph.compile()


def build_react_graph(deps: WorkflowDependencies | None = None, *, allowlist: set[str] | None = None):
    """Build a graph containing only the bounded ReAct investigation loop."""
    from langgraph.graph import END, START, StateGraph

    dependencies = deps or WorkflowDependencies()
    investigator = ReActInvestigator(
        build_default_registry(dependencies, allowlist),
        max_iterations=dependencies.settings.react_max_iterations,
        max_tool_calls=dependencies.settings.react_max_tool_calls,
    )
    graph = StateGraph(IntelligenceState)
    graph.add_node("react_investigator", investigator.step)
    graph.add_edge(START, "react_investigator")
    graph.add_conditional_edges(
        "react_investigator",
        lambda state: state.get("route", "budget_exit"),
        {"continue": "react_investigator", "normal_completion": END, "budget_exit": END},
    )
    return graph.compile()


class InvestigationGraph:
    """Compatibility wrapper exposing a simple run method."""

    def __init__(self, deps: WorkflowDependencies | None = None, nodes: list[Node] | None = None) -> None:
        self.deps = deps or WorkflowDependencies()
        self.nodes = nodes

    def compile(self):
        return build_langgraph(self.deps)

    def run(self, user_query: str) -> IntelligenceState:
        if self.nodes is not None:
            state = initial_state(user_query)
            for node in self.nodes:
                state.update(node(state))
            return state
        # Each research iteration traverses several nodes before the budget
        # gate can terminate the workflow. LangGraph's default recursion limit
        # of 25 is therefore too small for the configured default budget.
        recursion_limit = max(25, self.deps.settings.max_investigation_iterations * 10 + 10)
        return self.compile().invoke(
            initial_state(user_query),
            config={"recursion_limit": recursion_limit},
        )

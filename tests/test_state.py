import unittest

from argus.graph.state import initial_state


class IntelligenceStateTests(unittest.TestCase):
    def test_initial_state_contains_blueprint_fields(self) -> None:
        state = initial_state("Assess supplier exposure")
        self.assertEqual(state["user_query"], "Assess supplier exposure")
        self.assertEqual(state["investigation_iterations"], 0)
        self.assertIn("claims", state)
        self.assertIn("recommended_actions", state)


if __name__ == "__main__":
    unittest.main()


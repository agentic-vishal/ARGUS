import unittest

from argus.models.cascade import ModelRequest, TieredModelRouter


class Handler:
    def __init__(self, output="ok", fail=False):
        self.output, self.fail = output, fail

    def complete(self, request):
        if self.fail:
            raise RuntimeError("provider unavailable")
        return self.output


class CascadeTests(unittest.TestCase):
    def test_tasks_route_to_expected_tiers(self) -> None:
        router = TieredModelRouter({"tier_1": Handler(), "tier_2": Handler(), "tier_3": Handler()})
        self.assertEqual(router.tier_for(ModelRequest("relevance", "article")), "tier_1")
        self.assertEqual(router.tier_for(ModelRequest("claim_extraction", "claim")), "tier_2")
        self.assertEqual(router.tier_for(ModelRequest("recommendation", "action", material=True)), "tier_3")

    def test_low_confidence_escalates(self) -> None:
        router = TieredModelRouter({"tier_1": Handler(), "tier_2": Handler(), "tier_3": Handler()})
        self.assertEqual(router.tier_for(ModelRequest("relevance", "article", confidence=0.2)), "tier_2")

    def test_fallback_records_telemetry(self) -> None:
        router = TieredModelRouter({"tier_1": Handler(fail=True), "tier_2": Handler("recovered")})
        result = router.run(ModelRequest("relevance", "article"))
        self.assertEqual(result.output, "recovered")
        self.assertTrue(result.fallback_used)
        self.assertEqual(router.telemetry.summary()["call_count"], 1)
        self.assertGreater(result.estimated_cost, 0)


if __name__ == "__main__":
    unittest.main()

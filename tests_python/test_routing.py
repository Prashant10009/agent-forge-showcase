import unittest

from agent_forge_public.classification import classify
from agent_forge_public.models import Capability, RuntimeDescriptor, TaskSpec
from agent_forge_public.routing import CapabilityRouter, NoCompatibleRuntime


class ClassificationTests(unittest.TestCase):
    def test_classification_exposes_evidence(self) -> None:
        result = classify("Implement a Python function and debug it")
        self.assertEqual(result.kind, "code")
        self.assertIn("implement", result.evidence)
        self.assertIn(Capability.CODE, result.required)

    def test_unknown_work_has_safe_general_default(self) -> None:
        result = classify("Say hello")
        self.assertEqual(result.kind, "general")
        self.assertEqual(result.required, (Capability.TEXT,))


class RoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = CapabilityRouter()
        self.task = TaskSpec(
            "code-1",
            "Implement a parser",
            required=(Capability.TEXT, Capability.CODE),
            preferred=(Capability.TOOLS,),
        )

    def test_router_selects_compatible_runtime_and_explains_exclusions(self) -> None:
        runtimes = (
            RuntimeDescriptor("reasoner", frozenset({Capability.TEXT, Capability.REASONING})),
            RuntimeDescriptor(
                "code-runtime",
                frozenset({Capability.TEXT, Capability.CODE, Capability.TOOLS}),
                reliability=0.9,
                latency_ms=90,
                cost_tier=1,
            ),
        )
        decision = self.router.choose(self.task, runtimes)
        self.assertEqual(decision.runtime_name, "code-runtime")
        self.assertIn("missing code", decision.considered["reasoner"])
        self.assertEqual(decision.components["required"], 40.0)

    def test_router_refuses_incompatible_pool(self) -> None:
        runtimes = (RuntimeDescriptor("text-only", frozenset({Capability.TEXT})),)
        with self.assertRaises(NoCompatibleRuntime):
            self.router.choose(self.task, runtimes)

    def test_unavailable_runtime_is_never_selected(self) -> None:
        runtimes = (
            RuntimeDescriptor(
                "offline-code",
                frozenset({Capability.TEXT, Capability.CODE}),
                available=False,
            ),
            RuntimeDescriptor("online-code", frozenset({Capability.TEXT, Capability.CODE})),
        )
        decision = self.router.choose(self.task, runtimes)
        self.assertEqual(decision.runtime_name, "online-code")
        self.assertEqual(decision.considered["offline-code"], "excluded: unavailable")


if __name__ == "__main__":
    unittest.main()

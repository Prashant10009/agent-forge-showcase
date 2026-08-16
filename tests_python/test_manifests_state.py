import unittest
from concurrent.futures import ThreadPoolExecutor

from agent_forge_public.contracts import ActionRequest, LifecycleState, ManifestState, RiskLevel, RunIdentity
from agent_forge_public.manifests import (
    ManifestActionMismatch,
    ManifestOwnershipError,
    ManifestRegistry,
    ManifestReplay,
    action_fingerprint,
)
from agent_forge_public.models import ActionKind
from agent_forge_public.state import (
    ArtifactIntegrityError,
    ArtifactStore,
    InvalidTransition,
    TenantBoundaryError,
    TenantStateStore,
)


def identity(tenant="tenant", run="run", scope="turn"):
    return RunIdentity(run, tenant, "session", scope)


def action(text="hello"):
    return ActionRequest("inspect_text", {"text": text}, ActionKind.READ, RiskLevel.LOW)


class ManifestAndStateTests(unittest.TestCase):
    def test_fingerprint_is_key_order_independent(self):
        left = ActionRequest("x", {"a": 1, "b": 2}, ActionKind.READ, RiskLevel.LOW)
        right = ActionRequest("x", {"b": 2, "a": 1}, ActionKind.READ, RiskLevel.LOW)
        self.assertEqual(action_fingerprint((left,)), action_fingerprint((right,)))

    def test_same_pending_capability_is_reused(self):
        registry = ManifestRegistry()
        first, _ = registry.create_or_reuse(identity(), (action(),))
        second, disposition = registry.create_or_reuse(identity(), (action(),))
        self.assertEqual(first.manifest_id, second.manifest_id)
        self.assertEqual(disposition, "reused")

    def test_capability_is_never_reused_across_runs(self):
        registry = ManifestRegistry()
        first, _ = registry.create_or_reuse(identity(run="first"), (action(),))
        second, disposition = registry.create_or_reuse(identity(run="second"), (action(),))
        self.assertNotEqual(first.manifest_id, second.manifest_id)
        self.assertEqual(disposition, "created")

    def test_completed_capability_is_suppressed(self):
        registry = ManifestRegistry()
        manifest, _ = registry.create_or_reuse(identity(), (action(),))
        registry.approve(manifest.manifest_id, identity())
        registry.claim(manifest.manifest_id, identity(), (action(),))
        registry.complete(manifest.manifest_id, success=True)
        same, disposition = registry.create_or_reuse(identity(), (action(),))
        self.assertEqual(same.manifest_id, manifest.manifest_id)
        self.assertEqual(disposition, "suppressed")

    def test_owner_binding_covers_tenant_session_scope_and_run(self):
        registry = ManifestRegistry()
        manifest, _ = registry.create_or_reuse(identity(), (action(),))
        variants = (
            RunIdentity("run", "other", "session", "turn"),
            RunIdentity("run", "tenant", "other", "turn"),
            RunIdentity("run", "tenant", "session", "other"),
            RunIdentity("other", "tenant", "session", "turn"),
        )
        for wrong in variants:
            with self.assertRaises(ManifestOwnershipError):
                registry.approve(manifest.manifest_id, wrong)

    def test_claim_requires_exact_captured_actions(self):
        registry = ManifestRegistry()
        manifest, _ = registry.create_or_reuse(identity(), (action(),))
        registry.approve(manifest.manifest_id, identity())
        with self.assertRaises(ManifestActionMismatch):
            registry.claim(manifest.manifest_id, identity(), (action("changed"),))

    def test_one_claimant_wins_a_race(self):
        registry = ManifestRegistry()
        manifest, _ = registry.create_or_reuse(identity(), (action(),))
        registry.approve(manifest.manifest_id, identity())

        def claim_once(_):
            try:
                registry.claim(manifest.manifest_id, identity(), (action(),))
                return "claimed"
            except ManifestReplay:
                return "replayed"

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(claim_once, range(4)))
        self.assertEqual(results.count("claimed"), 1)
        self.assertEqual(results.count("replayed"), 3)

    def test_expired_manifest_cannot_be_approved(self):
        now = [10.0]
        registry = ManifestRegistry(1, clock=lambda: now[0])
        manifest, _ = registry.create_or_reuse(identity(), (action(),))
        now[0] = 12.0
        with self.assertRaises(ManifestReplay):
            registry.approve(manifest.manifest_id, identity())
        self.assertEqual(manifest.state, ManifestState.EXPIRED)

    def test_artifacts_are_content_addressed_and_repeatable(self):
        store = ArtifactStore()
        first = store.put("tenant", "report.txt", b"same")
        second = store.put("tenant", "report.txt", b"same")
        self.assertEqual(first, second)

    def test_artifact_read_enforces_tenant_boundary(self):
        store = ArtifactStore()
        ref = store.put("a", "report.txt", b"content")
        with self.assertRaises(TenantBoundaryError):
            store.get(ref.artifact_id, "b")

    def test_artifact_verification_recomputes_stored_bytes(self):
        store = ArtifactStore()
        ref = store.put("tenant", "report.txt", b"content", "text/plain")
        self.assertEqual(
            store.verify(
                ref.artifact_id,
                "tenant",
                expected_name="report.txt",
                expected_media_type="text/plain",
            ),
            ref,
        )
        store._content[ref.artifact_id] = b"tampered"
        with self.assertRaises(ArtifactIntegrityError):
            store.verify(ref.artifact_id, "tenant")

    def test_memory_queries_never_cross_tenants(self):
        state = TenantStateStore()
        state.append_memory("a", "s", "user", "architecture alpha")
        state.append_memory("b", "s", "user", "architecture beta")
        result = state.recent("a", query="architecture")
        self.assertEqual([item.tenant_id for item in result], ["a"])

    def test_checkpoint_history_is_monotonic(self):
        state = TenantStateStore()
        one = state.save_checkpoint("r", "t", "s", {"step": 1})
        two = state.save_checkpoint("r", "t", "s", {"step": 2})
        self.assertEqual((one.sequence, two.sequence), (1, 2))
        self.assertEqual(state.latest_checkpoint("r", "t"), two)

    def test_terminal_run_cannot_transition_again(self):
        state = TenantStateStore()
        state.transition("r", "t", LifecycleState.COMPLETED)
        with self.assertRaises(InvalidTransition):
            state.transition("r", "t", LifecycleState.RUNNING)


if __name__ == "__main__":
    unittest.main()

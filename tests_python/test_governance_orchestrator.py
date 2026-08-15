import unittest

from agent_forge_public.governance import ApprovalError, ApprovalGate
from agent_forge_public.models import ActionKind, RunStatus, TaskSpec
from agent_forge_public.orchestrator import AgentForge


class GovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = ApprovalGate(token_factory=lambda: "fixed-challenge")
        self.task = TaskSpec("write-1", "Write a file", action=ActionKind.WRITE)

    def test_side_effecting_action_uses_single_use_challenge(self) -> None:
        request = self.gate.request(self.task)
        self.gate.consume(request.approval_id, "fixed-challenge", task_id=self.task.task_id)
        with self.assertRaisesRegex(ApprovalError, "already been consumed"):
            self.gate.consume(request.approval_id, "fixed-challenge", task_id=self.task.task_id)

    def test_wrong_challenge_is_rejected(self) -> None:
        request = self.gate.request(self.task)
        with self.assertRaisesRegex(ApprovalError, "invalid"):
            self.gate.consume(request.approval_id, "wrong", task_id=self.task.task_id)


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.forge = AgentForge(approvals=ApprovalGate(token_factory=lambda: "approve-once"))

    def test_read_task_routes_and_executes(self) -> None:
        task = self.forge.make_task("Analyze the architecture", action=ActionKind.READ)
        outcome = self.forge.submit(task)
        self.assertEqual(outcome.status, RunStatus.COMPLETED)
        self.assertIsNotNone(outcome.result)
        self.assertEqual(outcome.trace[-1]["stage"], "verification")
        self.assertTrue(outcome.trace[-1]["details"]["non_empty_output"])

    def test_write_task_pauses_then_resumes(self) -> None:
        task = self.forge.make_task("Implement a Python parser", action=ActionKind.WRITE)
        pending = self.forge.submit(task)
        self.assertEqual(pending.status, RunStatus.APPROVAL_REQUIRED)
        self.assertIsNotNone(pending.approval)

        completed = self.forge.resume(pending.approval.approval_id, "approve-once")
        self.assertEqual(completed.status, RunStatus.COMPLETED)
        self.assertEqual(completed.route.runtime_name, "local-code")
        self.assertIn("completed task-1", completed.result.output)

        with self.assertRaises(KeyError):
            self.forge.resume(pending.approval.approval_id, "approve-once")


if __name__ == "__main__":
    unittest.main()

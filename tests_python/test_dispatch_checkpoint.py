import tempfile
import time
import unittest
from pathlib import Path

from agent_forge_public.checkpoint import JsonCheckpointStore
from agent_forge_public.dispatch import GraphDispatcher, InvalidTaskGraph, TaskGraph
from agent_forge_public.models import ActionKind, Capability, ExecutionResult, TaskSpec


def execute(task: TaskSpec) -> ExecutionResult:
    time.sleep(0.005)
    return ExecutionResult(task.task_id, "test-runtime", task.instruction.upper(), 5.0)


class TaskGraphTests(unittest.TestCase):
    def test_graph_builds_dependency_waves(self) -> None:
        graph = TaskGraph(
            (
                TaskSpec("inspect", "Inspect input"),
                TaskSpec("plan", "Plan change", depends_on=("inspect",)),
                TaskSpec("test", "Test result", depends_on=("plan",)),
                TaskSpec("document", "Document result", depends_on=("plan",)),
            )
        )
        self.assertEqual(
            tuple(tuple(task.task_id for task in wave) for wave in graph.waves()),
            (("inspect",), ("plan",), ("document", "test")),
        )

    def test_graph_rejects_cycles(self) -> None:
        with self.assertRaisesRegex(InvalidTaskGraph, "cycle"):
            TaskGraph(
                (
                    TaskSpec("a", "A", depends_on=("b",)),
                    TaskSpec("b", "B", depends_on=("a",)),
                )
            )

    def test_dispatch_executes_all_waves(self) -> None:
        graph = TaskGraph(
            (
                TaskSpec("a", "first"),
                TaskSpec("b", "second"),
                TaskSpec("c", "third", depends_on=("a", "b")),
            )
        )
        results = GraphDispatcher(execute, max_workers=2).run(graph)
        self.assertEqual(set(results), {"a", "b", "c"})
        self.assertEqual(results["c"].output, "THIRD")


class CheckpointTests(unittest.TestCase):
    def test_round_trip_and_missing_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonCheckpointStore(directory)
            self.assertIsNone(store.load("run-1"))
            path = store.save("run-1", {"status": "complete", "sequence": 4})
            self.assertTrue(path.exists())
            self.assertEqual(store.load("run-1")["sequence"], 4)

    def test_checkpoint_id_cannot_escape_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonCheckpointStore(directory)
            with self.assertRaises(ValueError):
                store.save("../outside", {"unsafe": True})
            self.assertFalse(Path(directory).parent.joinpath("outside.json").exists())


if __name__ == "__main__":
    unittest.main()

"""Evidence-admission behavior of the intentionally synthetic public example."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "examples" / "evaluation_learning_loop.py"
spec = importlib.util.spec_from_file_location("evaluation_learning_example", path)
example = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = example
spec.loader.exec_module(example)
Episode = example.Episode


class EvaluationLearningExampleTests(unittest.TestCase):
    def test_platform_error_does_not_teach_model_failure(self):
        result = example.collect((Episode("a", "t", "code", "r", True, False, "platform"),))
        self.assertEqual(result["accepted_outcomes"], [])
        self.assertEqual(result["audit"][0]["reason"], "availability_evidence_only")

    def test_unverified_and_assisted_successes_are_not_accepted(self):
        result = example.collect((
            Episode("a", "t", "code", "r", False, True, "completed"),
            Episode("b", "t", "code", "r", True, True, "completed", assisted=True),
        ))
        self.assertEqual(result["accepted_outcomes"], [])

    def test_verified_failure_remains_usable_evidence(self):
        result = example.collect((Episode("a", "t", "code", "r", True, False, "model"),))
        self.assertEqual(result["accepted_outcomes"][0]["failures"], 1)

    def test_duplicate_record_is_not_learned_twice(self):
        row = Episode("a", "t", "code", "r", True, True, "completed")
        result = example.collect((row, row))
        self.assertEqual(result["accepted_outcomes"][0]["successes"], 1)
        self.assertEqual(result["audit"][1]["reason"], "duplicate_episode")

    def test_task_families_and_tenants_do_not_mix(self):
        rows = tuple(Episode(str(i), tenant, task, "r", True, True, "completed")
                     for i, (tenant, task) in enumerate((("t1", "code"), ("t1", "research"), ("t2", "code"))))
        summaries = example.collect(rows)["accepted_outcomes"]
        self.assertEqual(len(summaries), 3)
        self.assertTrue(all(row["successes"] == 1 for row in summaries))

    def test_unknown_attribution_and_nonfinite_measurements_are_excluded(self):
        rows = (Episode("a", "t", "code", "r", True, False, "unknown"),
                Episode("b", "t", "code", "r", True, True, "completed", cost=float("nan")))
        self.assertEqual(example.collect(rows)["accepted_outcomes"], [])

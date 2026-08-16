import unittest

from agent_forge_public.state import TenantBoundaryError
from agent_forge_public.task_state import TenantTaskIndex, VectorContractError, VectorSpace


class TaskStateContractTests(unittest.TestCase):
    def test_dimension_mismatch_is_rejected(self):
        space = VectorSpace("public-task-state", 3)
        with self.assertRaises(VectorContractError):
            space.validate((1.0, 2.0))

    def test_non_finite_values_are_rejected(self):
        space = VectorSpace("public-task-state", 2)
        with self.assertRaises(VectorContractError):
            space.validate((1.0, float("nan")))

    def test_search_is_tenant_scoped(self):
        index = TenantTaskIndex()
        space = VectorSpace("public-task-state", 3)
        index.put("a-near", "tenant-a", space, (1, 0, 0), {"status": "complete"})
        index.put("b-near", "tenant-b", space, (1, 0, 0), {"status": "private"})
        results = index.search("tenant-a", space, (1, 0, 0))
        self.assertEqual([result.record_id for result in results], ["a-near"])

    def test_cross_tenant_direct_read_is_denied(self):
        index = TenantTaskIndex()
        space = VectorSpace("public-task-state", 2)
        index.put("task", "tenant-a", space, (1, 0))
        with self.assertRaises(TenantBoundaryError):
            index.get("task", "tenant-b")

    def test_ranking_is_deterministic(self):
        index = TenantTaskIndex()
        space = VectorSpace("public-task-state", 2)
        index.put("far", "tenant", space, (0, 1))
        index.put("near", "tenant", space, (1, 0))
        results = index.search("tenant", space, (1, 0))
        self.assertEqual([result.record_id for result in results], ["near", "far"])

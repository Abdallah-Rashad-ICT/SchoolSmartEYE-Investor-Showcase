import unittest

from scheduler import rank_workers, resource_score


class ResourceSchedulerTests(unittest.TestCase):
    def test_prefers_lower_cpu_and_memory_pressure(self):
        workers = [
            {"node_id": "PC2", "healthy": True,
             "capabilities": ["text_stats"],
             "metrics": {"load_per_cpu": 0.9,
                         "memory_available_bytes": 1, "memory_total_bytes": 100}},
            {"node_id": "PC3", "healthy": True,
             "capabilities": ["text_stats"],
             "metrics": {"load_per_cpu": 0.1,
                         "memory_available_bytes": 80, "memory_total_bytes": 100}},
        ]
        ranked = rank_workers(workers, "text_stats")
        self.assertEqual([item["node_id"] for item in ranked], ["PC3", "PC2"])

    def test_excludes_unhealthy_and_incapable_workers(self):
        workers = [
            {"node_id": "PC1", "healthy": False, "capabilities": ["echo"]},
            {"node_id": "PC2", "healthy": True, "capabilities": ["echo"]},
            {"node_id": "PC3", "healthy": True, "capabilities": ["text_stats"]},
        ]
        self.assertEqual(
            [item["node_id"] for item in rank_workers(workers, "text_stats")],
            ["PC3"],
        )

    def test_missing_telemetry_uses_neutral_fallback(self):
        self.assertEqual(resource_score({}), resource_score(None))


if __name__ == "__main__":
    unittest.main()

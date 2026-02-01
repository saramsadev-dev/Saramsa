import unittest

from work_items.services.devops_service import DevOpsService


class TestNarrationMerge(unittest.TestCase):
    def test_apply_llm_phrasing_by_candidate_id(self):
        service = DevOpsService.__new__(DevOpsService)
        items = [{
            "candidate_id": "c1",
            "title": "A",
            "description": "B",
            "priority": "medium",
            "type": "task",
        }]
        llm_items = [{
            "candidate_id": "c1",
            "title": "New Title",
            "description": "New Desc",
        }]
        merged = service._apply_llm_phrasing(items, llm_items)
        self.assertEqual(merged[0]["title"], "New Title")
        self.assertEqual(merged[0]["description"], "New Desc")


if __name__ == "__main__":
    unittest.main()

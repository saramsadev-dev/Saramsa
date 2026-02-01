import unittest

from feedback_analysis.services.narration_schema_validator import validate_narration_output


class TestNarrationSchemaValidator(unittest.TestCase):
    def test_valid_output(self):
        raw = {
            "insights": ["one", "two"],
            "features": [{"aspect_key": "pricing", "description": "desc"}],
            "work_items": [{"candidate_id": "c1", "title": "t", "description": "d"}],
        }
        parsed, errors = validate_narration_output(raw, ["pricing"], ["c1"])
        self.assertIsNotNone(parsed)
        self.assertEqual(errors, [])

    def test_reject_unknown_aspect(self):
        raw = {
            "insights": [],
            "features": [{"aspect_key": "unknown", "description": "desc"}],
            "work_items": [],
        }
        parsed, errors = validate_narration_output(raw, ["pricing"], [])
        self.assertIsNone(parsed)
        self.assertTrue(errors)

    def test_reject_unknown_candidate(self):
        raw = {
            "insights": [],
            "features": [],
            "work_items": [{"candidate_id": "bad", "title": "t", "description": "d"}],
        }
        parsed, errors = validate_narration_output(raw, [], ["c1"])
        self.assertIsNone(parsed)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()

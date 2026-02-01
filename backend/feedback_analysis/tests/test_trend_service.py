import unittest

from feedback_analysis.services.trend_service import TrendService


class TrendServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = TrendService()

    def test_stable_trend(self):
        analyses = [
            {"id": "a1", "analysis_id": "a1", "createdAt": "2026-01-01", "taxonomy_version": 1,
             "result": {"overall": {"negative": 30, "positive": 50, "neutral": 20},
                        "counts": {"total": 100},
                        "features": [{"name": "Pricing", "sentiment": {"negative": 40, "positive": 30}, "comment_count": 50}] }},
            {"id": "a2", "analysis_id": "a2", "createdAt": "2026-02-01", "taxonomy_version": 1,
             "result": {"overall": {"negative": 35, "positive": 45, "neutral": 20},
                        "counts": {"total": 120},
                        "features": [{"name": "Pricing", "sentiment": {"negative": 45, "positive": 25}, "comment_count": 60}] }},
        ]
        overall = self.service._build_overall_series(analyses)
        aspects = self.service._build_aspect_series(analyses)
        self.assertEqual(len(overall), 2)
        self.assertEqual(aspects[0]["status"], "stable")

    def test_partial_trend(self):
        analyses = [
            {"id": "a1", "analysis_id": "a1", "createdAt": "2026-01-01", "taxonomy_version": 1,
             "result": {"features": [{"name": "Pricing", "sentiment": {"negative": 40}, "comment_count": 50}] }},
            {"id": "a2", "analysis_id": "a2", "createdAt": "2026-02-01", "taxonomy_version": 2,
             "result": {"features": [{"name": "Support", "sentiment": {"negative": 50}, "comment_count": 30}] }},
        ]
        aspects = self.service._build_aspect_series(analyses)
        pricing = [a for a in aspects if a["aspect_key"] == "pricing"][0]
        self.assertEqual(pricing["status"], "partial")

    def test_missing_aspect(self):
        analyses = [
            {"id": "a1", "analysis_id": "a1", "createdAt": "2026-01-01", "taxonomy_version": 1,
             "result": {"features": []}},
        ]
        series, coverage, versions, _ = self.service._build_single_aspect_series(analyses, "pricing")
        self.assertEqual(series, [])
        self.assertEqual(coverage["present"], 0)
        self.assertEqual(coverage["total"], 1)

    def test_alert_generation(self):
        overall = [
            {"analysis_id": "a1", "unmapped": 0.0},
            {"analysis_id": "a2", "unmapped": 0.2},
        ]
        aspects = [
            {"aspect_key": "pricing", "series": [
                {"analysis_id": "a1", "neg_pct": 0.2},
                {"analysis_id": "a2", "neg_pct": 0.35},
            ], "coverage": {"present": 2, "total": 2}}
        ]
        alerts = self.service._build_alerts(overall, aspects)
        self.assertTrue(any(a["type"] == "unmapped_surge" for a in alerts))
        self.assertTrue(any(a["type"] == "spike" for a in alerts))


if __name__ == "__main__":
    unittest.main()

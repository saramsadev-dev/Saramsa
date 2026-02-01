"""
Trend analytics service (Phase-5).

Computes project-level and aspect-level trends from stored analysis aggregates.
No ML or LLM calls.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ..repositories import AnalysisRepository

logger = logging.getLogger(__name__)


class TrendService:
    """Compute taxonomy-aware trends from stored analyses."""

    def __init__(self):
        self.analysis_repo = AnalysisRepository()

    def get_project_trends(self, project_id: str, limit: int = 20) -> Dict[str, Any]:
        analyses = self._get_recent_analyses(project_id, limit)
        if len(analyses) <= 1:
            return {
                "project_id": project_id,
                "window": {"limit": limit},
                "overall": [],
                "aspects": [],
                "alerts": [],
                "message": "Not enough analyses for trends"
            }

        overall_series = self._build_overall_series(analyses)
        aspect_series = self._build_aspect_series(analyses)
        alerts = self._build_alerts(overall_series, aspect_series)

        return {
            "project_id": project_id,
            "window": {"limit": limit},
            "overall": overall_series,
            "aspects": aspect_series,
            "alerts": alerts,
        }

    def get_aspect_trend(self, project_id: str, aspect_key: str, limit: int = 20) -> Dict[str, Any]:
        analyses = self._get_recent_analyses(project_id, limit)
        key = self._normalize_aspect_key(aspect_key)
        series, coverage, versions, label = self._build_single_aspect_series(analyses, key)
        status = "stable" if coverage["present"] == coverage["total"] else "partial"
        return {
            "project_id": project_id,
            "aspect_key": key,
            "label": label or aspect_key,
            "coverage": coverage,
            "versions": versions,
            "series": series,
            "status": status,
        }

    def _get_recent_analyses(self, project_id: str, limit: int) -> List[Dict[str, Any]]:
        analyses = self.analysis_repo.get_recent_by_project(project_id, limit)
        # Ascending by createdAt for time series
        return sorted(analyses, key=lambda a: a.get("createdAt") or a.get("analysis_date") or "")

    def _build_overall_series(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        series = []
        for a in analyses:
            result = a.get("result") or a.get("analysisData") or {}
            overall = result.get("overall") or result.get("overall_sentiment") or {}
            counts = result.get("counts") or {}
            series.append({
                "analysis_id": a.get("analysis_id") or a.get("id"),
                "ts": a.get("createdAt") or a.get("analysis_date"),
                "neg_pct": self._to_ratio(overall.get("negative")),
                "pos_pct": self._to_ratio(overall.get("positive")),
                "neu_pct": self._to_ratio(overall.get("neutral")),
                "count": counts.get("total"),
                "unmapped": self._extract_unmapped_rate(result),
                "taxonomy_version": a.get("taxonomy_version"),
                "pipeline_status": self._extract_pipeline_status(a),
            })
        return series

    def _build_aspect_series(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        aspect_map: Dict[str, Dict[str, Any]] = {}
        total = len(analyses)

        for a in analyses:
            result = a.get("result") or a.get("analysisData") or {}
            features = result.get("features") or []
            for f in features:
                if not isinstance(f, dict):
                    continue
                name = f.get("key") or f.get("name") or f.get("feature")
                if not name:
                    continue
                aspect_key = self._normalize_aspect_key(name)
                entry = aspect_map.setdefault(aspect_key, {
                    "aspect_key": aspect_key,
                    "label": name,
                    "series": [],
                    "present": 0,
                    "versions": set(),
                })
                entry["present"] += 1
                entry["versions"].add(a.get("taxonomy_version"))
                sentiment = f.get("sentiment") or {}
                entry["series"].append({
                    "analysis_id": a.get("analysis_id") or a.get("id"),
                    "ts": a.get("createdAt") or a.get("analysis_date"),
                    "neg_pct": self._to_ratio(sentiment.get("negative")),
                    "pos_pct": self._to_ratio(sentiment.get("positive")),
                    "count": f.get("comment_count") or f.get("total_mentions"),
                    "taxonomy_version": a.get("taxonomy_version"),
                })

        aspects = []
        for aspect_key, data in aspect_map.items():
            aspects.append({
                "aspect_key": aspect_key,
                "label": data["label"],
                "coverage": {"present": data["present"], "total": total},
                "versions": sorted([v for v in data["versions"] if v is not None]),
                "series": data["series"],
                "status": "stable" if data["present"] == total else "partial",
            })

        # Sort by volume (latest count desc)
        aspects.sort(key=lambda a: (a["series"][-1].get("count") or 0), reverse=True)
        return aspects[:10]

    def _build_single_aspect_series(self, analyses: List[Dict[str, Any]], aspect_key: str):
        series = []
        present = 0
        versions = set()
        label = None
        total = len(analyses)
        for a in analyses:
            result = a.get("result") or a.get("analysisData") or {}
            features = result.get("features") or []
            for f in features:
                if not isinstance(f, dict):
                    continue
                name = f.get("key") or f.get("name") or f.get("feature")
                if not name:
                    continue
                if self._normalize_aspect_key(name) != aspect_key:
                    continue
                label = name
                present += 1
                versions.add(a.get("taxonomy_version"))
                sentiment = f.get("sentiment") or {}
                series.append({
                    "analysis_id": a.get("analysis_id") or a.get("id"),
                    "ts": a.get("createdAt") or a.get("analysis_date"),
                    "neg_pct": self._to_ratio(sentiment.get("negative")),
                    "pos_pct": self._to_ratio(sentiment.get("positive")),
                    "count": f.get("comment_count") or f.get("total_mentions"),
                    "taxonomy_version": a.get("taxonomy_version"),
                })
        coverage = {"present": present, "total": total}
        return series, coverage, sorted([v for v in versions if v is not None]), label

    def _build_alerts(self, overall_series: List[Dict[str, Any]], aspect_series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alerts = []
        if len(overall_series) >= 2:
            last = overall_series[-1]
            prev = overall_series[-2]
            delta_unmapped = (last.get("unmapped") or 0) - (prev.get("unmapped") or 0)
            if delta_unmapped >= 0.10:
                alerts.append({
                    "type": "unmapped_surge",
                    "delta_unmapped": round(delta_unmapped, 2),
                    "since_analysis_id": prev.get("analysis_id"),
                })
        for aspect in aspect_series:
            series = aspect.get("series", [])
            if len(series) < 2:
                continue
            last = series[-1]
            prev = series[-2]
            delta_neg = (last.get("neg_pct") or 0) - (prev.get("neg_pct") or 0)
            if delta_neg >= 0.10:
                alerts.append({
                    "type": "spike",
                    "aspect_key": aspect.get("aspect_key"),
                    "delta_neg_pct": round(delta_neg, 2),
                    "since_analysis_id": prev.get("analysis_id"),
                })
            # Emerging theme: appears only in latest
            if aspect.get("coverage", {}).get("present") == 1:
                alerts.append({
                    "type": "emerging",
                    "aspect_key": aspect.get("aspect_key"),
                    "first_seen": last.get("ts"),
                })
        return alerts

    def _extract_unmapped_rate(self, result: Dict[str, Any]) -> Optional[float]:
        metadata = result.get("pipeline_metadata") or result.get("pipelineMetadata")
        if isinstance(metadata, dict) and metadata.get("unmapped_percentage") is not None:
            return float(metadata.get("unmapped_percentage"))
        if result.get("unmapped_rate") is not None:
            return float(result.get("unmapped_rate"))
        return None

    def _extract_pipeline_status(self, analysis: Dict[str, Any]) -> Optional[str]:
        narration = analysis.get("narration") or {}
        meta = narration.get("_meta") if isinstance(narration, dict) else None
        if isinstance(meta, dict) and meta.get("status") == "FALLBACK":
            return "PARTIAL"
        return "COMPLETE"

    @staticmethod
    def _normalize_aspect_key(label: str) -> str:
        return str(label).strip().lower().replace(" ", "_")

    @staticmethod
    def _to_ratio(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            v = float(value)
        except Exception:
            return 0.0
        return v / 100.0 if v > 1.0 else v


_trend_service = None


def get_trend_service() -> TrendService:
    """Get the global TrendService instance."""
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService()
    return _trend_service

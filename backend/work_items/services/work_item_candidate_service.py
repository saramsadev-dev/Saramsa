"""
Rule-first work item candidate generation (Phase-2).

Deterministic rules produce WorkItemCandidate objects from analysis metrics.
LLMs may only phrase candidates and must not decide existence, type, or priority.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class WorkItemCandidateService:
    """Deterministic work item candidate generator."""

    # Rule Group A thresholds
    NEGATIVE_CREATE_THRESHOLD = 0.40
    NEGATIVE_PRIORITY_P0 = 0.55
    NEGATIVE_PRIORITY_P1 = 0.40
    NEGATIVE_MIN_COMMENTS = 20

    # Rule Group B thresholds
    MIXED_CREATE_THRESHOLD = 0.30
    MIXED_MIN_COMMENTS = 30

    # Rule Group D thresholds
    TAXONOMY_GAP_UNMAPPED_THRESHOLD = 0.15

    # Known bug aspect keys (project-specific in future)
    KNOWN_BUG_ASPECT_KEYS = set()  # TODO(phase-3): load from project config

    PRIORITY_ORDER = ["P3", "P2", "P1", "P0"]

    def generate_candidates(self, analysis: Dict[str, Any], previous_analysis: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate deterministic candidates from analysis metrics only."""
        features = self._extract_features(analysis)
        if not features:
            return []

        project_id = self._get_analysis_field(analysis, "project_id") or self._get_analysis_field(analysis, "projectId")
        analysis_id = self._get_analysis_field(analysis, "analysis_id") or self._get_analysis_field(analysis, "id")
        taxonomy_id = self._get_analysis_field(analysis, "taxonomy_id")
        taxonomy_version = self._get_analysis_field(analysis, "taxonomy_version")

        previous_map = self._build_previous_neg_map(previous_analysis)

        candidates: List[Dict[str, Any]] = []
        for feature in features:
            aspect_key, metrics = self._feature_metrics(feature)
            if not aspect_key:
                continue

            neg_pct = metrics.get("neg_pct", 0.0)
            mixed_pct = metrics.get("mixed_pct", 0.0)
            comment_count = metrics.get("comment_count", 0)
            confidence_p95 = metrics.get("confidence_p95")

            # Rule Group A — Negative sentiment
            if neg_pct >= self.NEGATIVE_CREATE_THRESHOLD and comment_count >= self.NEGATIVE_MIN_COMMENTS:
                priority = self._priority_from_negative(neg_pct)
                candidate_type = "bug" if aspect_key in self.KNOWN_BUG_ASPECT_KEYS else "improvement"
                candidates.append(self._build_candidate(
                    project_id=project_id,
                    analysis_id=analysis_id,
                    taxonomy_id=taxonomy_id,
                    taxonomy_version=taxonomy_version,
                    aspect_key=aspect_key,
                    candidate_type=candidate_type,
                    priority=priority,
                    reason={
                        "neg_pct": neg_pct,
                        "comment_count": comment_count,
                        "trend": self._trend_direction(neg_pct, previous_map.get(aspect_key)),
                        "confidence_p95": confidence_p95,
                    },
                    evidence=self._extract_evidence(feature),
                ))
                continue

            # Rule Group B — Mixed/ambiguous sentiment
            if mixed_pct >= self.MIXED_CREATE_THRESHOLD and comment_count >= self.MIXED_MIN_COMMENTS:
                candidates.append(self._build_candidate(
                    project_id=project_id,
                    analysis_id=analysis_id,
                    taxonomy_id=taxonomy_id,
                    taxonomy_version=taxonomy_version,
                    aspect_key=aspect_key,
                    candidate_type="ux",
                    priority="P2",
                    reason={
                        "neg_pct": neg_pct,
                        "comment_count": comment_count,
                        "trend": self._trend_direction(neg_pct, previous_map.get(aspect_key)),
                        "confidence_p95": confidence_p95,
                    },
                    evidence=self._extract_evidence(feature),
                ))

        # Rule Group D — Taxonomy gaps
        unmapped_rate = self._extract_unmapped_rate(analysis)
        if unmapped_rate is not None and unmapped_rate >= self.TAXONOMY_GAP_UNMAPPED_THRESHOLD:
            candidates.append(self._build_candidate(
                project_id=project_id,
                analysis_id=analysis_id,
                taxonomy_id=taxonomy_id,
                taxonomy_version=taxonomy_version,
                aspect_key="__taxonomy__",
                candidate_type="taxonomy_gap",
                priority="P2",
                reason={
                    "neg_pct": 0.0,
                    "comment_count": self._total_comment_count(analysis),
                    "trend": "flat",
                    "confidence_p95": None,
                },
                evidence=[],
            ))

        # Rule Group C — Trend escalation
        candidates = [self._apply_trend_escalation(c, previous_map) for c in candidates]

        return candidates

    def _apply_trend_escalation(self, candidate: Dict[str, Any], previous_map: Dict[str, float]) -> Dict[str, Any]:
        """Escalate priority if negative sentiment rose >=10% vs previous analysis."""
        aspect_key = candidate.get("aspect_key")
        prev_neg = previous_map.get(aspect_key)
        curr_neg = candidate.get("reason", {}).get("neg_pct")
        if prev_neg is None or curr_neg is None:
            return candidate
        if (curr_neg - prev_neg) >= 0.10:
            candidate = candidate.copy()
            candidate["priority"] = self._escalate_priority(candidate.get("priority"))
        return candidate

    def _build_candidate(
        self,
        project_id: Optional[str],
        analysis_id: Optional[str],
        taxonomy_id: Optional[str],
        taxonomy_version: Optional[int],
        aspect_key: str,
        candidate_type: str,
        priority: str,
        reason: Dict[str, Any],
        evidence: List[str],
    ) -> Dict[str, Any]:
        return {
            "candidate_id": str(uuid.uuid4()),
            "project_id": project_id,
            "analysis_id": analysis_id,
            "taxonomy_id": taxonomy_id,
            "taxonomy_version": taxonomy_version,
            "aspect_key": aspect_key,
            "type": candidate_type,
            "priority": priority,
            "reason": reason,
            "evidence": evidence,
            "created_by": "rules_engine",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _priority_from_negative(self, neg_pct: float) -> str:
        if neg_pct >= self.NEGATIVE_PRIORITY_P0:
            return "P0"
        if neg_pct >= self.NEGATIVE_PRIORITY_P1:
            return "P1"
        return "P2"

    def _escalate_priority(self, priority: str) -> str:
        if priority not in self.PRIORITY_ORDER:
            return priority
        idx = self.PRIORITY_ORDER.index(priority)
        return self.PRIORITY_ORDER[min(idx + 1, len(self.PRIORITY_ORDER) - 1)]

    def _trend_direction(self, current: Optional[float], previous: Optional[float]) -> str:
        if current is None or previous is None:
            return "flat"
        if (current - previous) >= 0.10:
            return "up"
        if (previous - current) >= 0.10:
            return "down"
        return "flat"

    def _extract_features(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(analysis, dict):
            return []
        for source in (analysis, analysis.get("analysisData")):
            if isinstance(source, dict):
                feats = source.get("features") or source.get("featureasba") or source.get("feature_asba")
                if isinstance(feats, list):
                    return feats
        return []

    def _feature_metrics(self, feature: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        if not isinstance(feature, dict):
            return None, {}
        name = feature.get("key") or feature.get("name") or feature.get("feature")
        aspect_key = self._normalize_aspect_key(name) if name else None

        sentiment = feature.get("sentiment") or {}
        neg_pct = self._to_ratio(sentiment.get("negative"))
        mixed_pct = self._to_ratio(sentiment.get("mixed"))
        comment_count = feature.get("comment_count") or feature.get("commentcount") or feature.get("total_mentions") or 0
        try:
            comment_count = int(comment_count)
        except Exception:
            comment_count = 0

        return aspect_key, {
            "neg_pct": neg_pct,
            "mixed_pct": mixed_pct,
            "comment_count": comment_count,
            "confidence_p95": None,
        }

    def _extract_unmapped_rate(self, analysis: Dict[str, Any]) -> Optional[float]:
        if not isinstance(analysis, dict):
            return None
        for source in (analysis, analysis.get("analysisData")):
            if isinstance(source, dict):
                metadata = source.get("pipeline_metadata") or source.get("pipelineMetadata")
                if isinstance(metadata, dict):
                    val = metadata.get("unmapped_percentage")
                    if val is not None:
                        return float(val)
        return None

    def _total_comment_count(self, analysis: Dict[str, Any]) -> int:
        if not isinstance(analysis, dict):
            return 0
        for source in (analysis, analysis.get("analysisData")):
            if isinstance(source, dict):
                counts = source.get("counts")
                if isinstance(counts, dict) and counts.get("total") is not None:
                    try:
                        return int(counts.get("total"))
                    except Exception:
                        return 0
        return 0

    def _extract_evidence(self, feature: Dict[str, Any]) -> List[str]:
        # Deterministic, text-only evidence (no LLM). Uses keywords if available.
        keywords = feature.get("keywords") if isinstance(feature, dict) else None
        if isinstance(keywords, list) and keywords:
            return [f"Keyword: {k}" for k in keywords[:2]]
        return []

    def _build_previous_neg_map(self, previous_analysis: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not isinstance(previous_analysis, dict):
            return {}
        features = self._extract_features(previous_analysis)
        prev_map = {}
        for feature in features:
            aspect_key, metrics = self._feature_metrics(feature)
            if aspect_key:
                prev_map[aspect_key] = metrics.get("neg_pct", 0.0)
        return prev_map

    def _get_analysis_field(self, analysis: Dict[str, Any], field: str) -> Any:
        """Look up a field in the analysis dict or its nested analysisData."""
        if not isinstance(analysis, dict):
            return None
        for source in (analysis, analysis.get("analysisData"), analysis.get("result")):
            if isinstance(source, dict) and source.get(field) is not None:
                return source[field]
        return None

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
        # Accept either 0-1 or 0-100 inputs
        return v / 100.0 if v > 1.0 else v


_candidate_service = None


def get_work_item_candidate_service() -> WorkItemCandidateService:
    """Get the global WorkItemCandidateService instance."""
    global _candidate_service
    if _candidate_service is None:
        _candidate_service = WorkItemCandidateService()
    return _candidate_service

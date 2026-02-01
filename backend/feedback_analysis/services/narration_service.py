"""
Unified narration service (Phase-3).

Single GPT entrypoint for narrative text.
Deterministic inputs are trimmed and validated before/after the call.
"""

from typing import Dict, Any, List, Optional
import logging

from asgiref.sync import async_to_sync
from datetime import datetime
import os
from aiCore.services.completion_service import generate_completions
from apis.infrastructure.cache_service import get_cache_service
from .usage_service import get_usage_service
from apis.prompts.narration_prompt import create_narration_prompt
from .narration_schema_validator import validate_narration_output

logger = logging.getLogger(__name__)


class NarrationService:
    """Generate narrative text for analysis and work items."""

    MAX_EVIDENCE = 30
    MAX_KEYWORDS_PER_ASPECT = 5
    MAX_OUTPUT_TOKENS = 1200
    last_status = None
    last_errors = None
    last_cost = None

    def generate_narratives(self, narration_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narratives with strict schema validation and deterministic trimming."""
        trimmed = self._trim_input(narration_input)
        project_id = trimmed.get("project_id")
        analysis_id = trimmed.get("analysis_id")
        cache = get_cache_service()

        # Hard cap: max narration calls per analysis = 1
        if analysis_id:
            if cache.get(f"narration_called:{analysis_id}"):
                self.last_status = "HARD_CAP"
                self.last_errors = ["max_narration_calls_per_analysis exceeded"]
                result = self._fallback(trimmed)
                result["_meta"] = {"status": "HARD_CAP", "errors": self.last_errors}
                return result
            cache.set(f"narration_called:{analysis_id}", True, ttl=86400)

        # Soft budgets + abuse throttles (skip narration only)
        if project_id and self._budget_exceeded(project_id):
            self.last_status = "BUDGET_EXCEEDED"
            self.last_errors = ["budget_exceeded"]
            result = self._fallback(trimmed)
            result["_meta"] = {"status": "BUDGET_EXCEEDED", "errors": self.last_errors}
            return result
        if project_id and self._throttle_exceeded(project_id):
            self.last_status = "THROTTLED"
            self.last_errors = ["throttled"]
            result = self._fallback(trimmed)
            result["_meta"] = {"status": "THROTTLED", "errors": self.last_errors}
            return result
        if analysis_id and cache.get(f"analysis_failed:{analysis_id}"):
            self.last_status = "THROTTLED"
            self.last_errors = ["failed_analysis_retry"]
            result = self._fallback(trimmed)
            result["_meta"] = {"status": "THROTTLED", "errors": self.last_errors}
            return result
        prompt = create_narration_prompt(trimmed)

        try:
            raw = async_to_sync(generate_completions)(prompt, max_tokens=self.MAX_OUTPUT_TOKENS)
            parsed, errors = validate_narration_output(
                raw,
                allowed_aspect_keys=[f.get("aspect_key") for f in trimmed.get("features", [])],
                allowed_candidate_ids=[c.get("candidate_id") for c in trimmed.get("work_item_candidates", [])],
            )
            if parsed is None:
                logger.warning("Narration validation failed, using fallback: %s", errors)
                self.last_status = "FALLBACK"
                self.last_errors = errors
                result = self._fallback(trimmed)
                result["_meta"] = {"status": "FALLBACK", "errors": errors}
                return result
            self.last_status = "OK"
            self.last_errors = None
            parsed["_meta"] = {"status": "OK"}
            self._record_usage(project_id, prompt, raw, cache_hit=False)
            self._increment_usage_counters(project_id, prompt, raw)
            return parsed
        except Exception as e:
            logger.warning(f"Narration generation failed, using fallback: {e}")
            self.last_status = "FALLBACK"
            self.last_errors = [str(e)]
            result = self._fallback(trimmed)
            result["_meta"] = {"status": "FALLBACK", "errors": [str(e)]}
            return result

    def _trim_input(self, narration_input: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministically trim evidence and keywords to budgets."""
        trimmed = dict(narration_input)

        # Trim keywords per aspect
        features = []
        for f in narration_input.get("features", []) or []:
            if not isinstance(f, dict):
                continue
            keywords = f.get("keywords") or []
            if isinstance(keywords, list):
                keywords = keywords[: self.MAX_KEYWORDS_PER_ASPECT]
            f = dict(f)
            f["keywords"] = keywords
            features.append(f)
        trimmed["features"] = features

        # Trim evidence: highest confidence first, cap total
        evidence = narration_input.get("evidence") or []
        evidence_sorted = sorted(
            [e for e in evidence if isinstance(e, dict)],
            key=lambda x: float(x.get("confidence", 0.0)),
            reverse=True,
        )
        trimmed["evidence"] = evidence_sorted[: self.MAX_EVIDENCE]

        return trimmed

    def _fallback(self, narration_input: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic fallback narratives."""
        insights = [
            "Analysis completed using deterministic metrics.",
            "Review feature-level sentiment for actionable areas.",
            "Prioritize items based on negative sentiment and volume.",
        ]
        features = [
            {
                "aspect_key": f.get("aspect_key"),
                "description": f"Customer feedback about {f.get('aspect_key')}.",
            }
            for f in narration_input.get("features", [])
            if isinstance(f, dict) and f.get("aspect_key")
        ]
        work_items = [
            {
                "candidate_id": c.get("candidate_id"),
                "title": f"Address {c.get('aspect_key')} feedback",
                "description": "Review evidence and address customer concerns.",
            }
            for c in narration_input.get("work_item_candidates", [])
            if isinstance(c, dict) and c.get("candidate_id")
        ]
        return {
            "insights": insights[:5],
            "features": features,
            "work_items": work_items,
        }

    def _record_usage(self, project_id: Optional[str], prompt: str, output: Any, cache_hit: bool) -> None:
        if not project_id:
            return
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(output if isinstance(output, str) else "")
        period_day = datetime.now().strftime("%Y-%m-%d")
        period_month = datetime.now().strftime("%Y-%m")
        usage_service = get_usage_service()
        usage_service.record_narration_usage(project_id, period_day, input_tokens, output_tokens, cache_hit=cache_hit)
        usage_service.record_narration_usage(project_id, period_month, input_tokens, output_tokens, cache_hit=cache_hit)
        self.last_cost = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    def _increment_usage_counters(self, project_id: Optional[str], prompt: str, output: Any) -> None:
        if not project_id:
            return
        cache = get_cache_service()
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(output if isinstance(output, str) else "")
        cache.incr(f"usage_calls:{project_id}:{day}", 1, ttl=86400)
        cache.incr(f"usage_calls:{project_id}:{month}", 1, ttl=2592000)
        cache.incr(f"usage_tokens:{project_id}:{month}", input_tokens + output_tokens, ttl=2592000)

    @staticmethod
    def _estimate_tokens(text: Any) -> int:
        if not text:
            return 0
        s = str(text)
        return int(len(s.split()) * 1.3)

    @staticmethod
    def _budget_exceeded(project_id: str) -> bool:
        cache = get_cache_service()
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")
        max_day = int(os.getenv("MAX_NARRATION_CALLS_PER_DAY", "0") or "0")
        max_month = int(os.getenv("MAX_NARRATION_CALLS_PER_MONTH", "0") or "0")
        max_tokens = int(os.getenv("MAX_NARRATION_TOKENS_PER_MONTH", "0") or "0")
        if max_day > 0 and cache.get(f"usage_calls:{project_id}:{day}", 0) >= max_day:
            return True
        if max_month > 0 and cache.get(f"usage_calls:{project_id}:{month}", 0) >= max_month:
            return True
        if max_tokens > 0 and cache.get(f"usage_tokens:{project_id}:{month}", 0) >= max_tokens:
            return True
        return False

    @staticmethod
    def _throttle_exceeded(project_id: str) -> bool:
        cache = get_cache_service()
        hour = datetime.now().strftime("%Y-%m-%d-%H")
        max_per_hour = int(os.getenv("MAX_ANALYSES_PER_HOUR", "0") or "0")
        if max_per_hour > 0 and cache.get(f"analyses_hour:{project_id}:{hour}", 0) > max_per_hour:
            return True
        return False


_narration_service = None


def get_narration_service() -> NarrationService:
    """Get the global narration service instance."""
    global _narration_service
    if _narration_service is None:
        _narration_service = NarrationService()
    return _narration_service

"""
Unified narration service (Phase-3).

Single GPT entrypoint for narrative text.
Deterministic inputs are trimmed and validated before/after the call.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

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
    MAX_OUTPUT_TOKENS = 2500
    last_status = None
    last_errors = None
    last_cost = None

    def generate_narratives(self, narration_input: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate narratives with strict schema validation and deterministic trimming.

        Raises on failure so callers see the real error instead of silent mock data.
        """
        trimmed = self._trim_input(narration_input)
        project_id = trimmed.get("project_id")
        analysis_id = trimmed.get("analysis_id")
        cache = get_cache_service()

        if analysis_id:
            if cache.get(f"narration_called:{analysis_id}"):
                raise RuntimeError("max_narration_calls_per_analysis exceeded")
            cache.set(f"narration_called:{analysis_id}", True, ttl=86400)

        if project_id and self._budget_exceeded(project_id):
            raise RuntimeError("Narration budget exceeded for this project")
        if project_id and self._throttle_exceeded(project_id):
            raise RuntimeError("Narration throttle exceeded for this project")
        if analysis_id and cache.get(f"analysis_failed:{analysis_id}"):
            raise RuntimeError("Cannot narrate a previously failed analysis")

        prompt = create_narration_prompt(trimmed)

        raw, actual_usage = self._call_generate_completions(prompt, user_id=user_id, project_id=project_id)
        parsed, errors = validate_narration_output(
            raw,
            allowed_aspect_keys=[f.get("aspect_key") for f in trimmed.get("features", [])],
            allowed_candidate_ids=[c.get("candidate_id") for c in trimmed.get("work_item_candidates", [])],
        )
        if parsed is None:
            raise RuntimeError(f"Narration validation failed: {errors}")

        self.last_status = "OK"
        self.last_errors = None
        parsed["_meta"] = {"status": "OK"}
        self._record_usage(project_id, user_id, actual_usage, cache_hit=False)
        self._increment_usage_counters(project_id, actual_usage)
        return parsed

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

    def _call_generate_completions(self, prompt: str, user_id: Optional[str] = None, project_id: Optional[str] = None):
        """Call async generate_completions from sync code. Safe when already inside an async event loop."""
        def _run():
            return async_to_sync(generate_completions)(
                prompt, max_tokens=self.MAX_OUTPUT_TOKENS,
                user_id=user_id, project_id=project_id, task_type="narration",
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return _run()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            return future.result()

    def _record_usage(self, project_id: Optional[str], user_id: Optional[str],
                      actual_usage: Optional[Dict[str, Any]], cache_hit: bool) -> None:
        if not project_id:
            return
        input_tokens = (actual_usage or {}).get("input_tokens") or 0
        output_tokens = (actual_usage or {}).get("output_tokens") or 0
        period_day = datetime.now().strftime("%Y-%m-%d")
        period_month = datetime.now().strftime("%Y-%m")
        usage_service = get_usage_service()
        usage_service.record_narration_usage(
            project_id, period_day, input_tokens, output_tokens,
            cache_hit=cache_hit, user_id=user_id,
        )
        usage_service.record_narration_usage(
            project_id, period_month, input_tokens, output_tokens,
            cache_hit=cache_hit, user_id=user_id,
        )
        self.last_cost = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    def _increment_usage_counters(self, project_id: Optional[str], actual_usage: Optional[Dict[str, Any]]) -> None:
        if not project_id:
            return
        cache = get_cache_service()
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")
        input_tokens = (actual_usage or {}).get("input_tokens") or 0
        output_tokens = (actual_usage or {}).get("output_tokens") or 0
        cache.incr(f"usage_calls:{project_id}:{day}", 1, ttl=86400)
        cache.incr(f"usage_calls:{project_id}:{month}", 1, ttl=2592000)
        cache.incr(f"usage_tokens:{project_id}:{month}", input_tokens + output_tokens, ttl=2592000)

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

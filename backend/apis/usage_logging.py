import logging
from typing import Optional, Dict, Any

from opentelemetry import trace

from .request_context import request_id_var, token_usage_var
from .otel import log_custom_event


logger = logging.getLogger("apis.app")


def _hex_trace_ids() -> Dict[str, Optional[str]]:
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        if ctx and ctx.is_valid:
            return {
                "trace_id": format(ctx.trace_id, "032x"),
                "span_id": format(ctx.span_id, "016x"),
            }
    except Exception:
        pass
    return {"trace_id": None, "span_id": None}


def log_token_usage(
    *,
    request=None,
    model: Optional[str] = None,
    vendor: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log custom token usage event (file/Log Analytics) and emit OTEL event.

    Call this right after an LLM call returns usage. Safe for production; does not log
    prompts/outputs, only counts, cost, and identifiers.
    """
    try:
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)

        req_id = None
        method = path = user_id = None
        if request is not None:
            try:
                req_id = getattr(request, "request_id", None) or request.headers.get("X-Request-ID")
            except Exception:
                req_id = None
            try:
                method = request.method
                path = request.path
            except Exception:
                pass
            try:
                user_id = getattr(request.user, "id", None) if getattr(request, "user", None) and request.user.is_authenticated else None
            except Exception:
                user_id = None

        req_id = req_id or request_id_var.get()

        trace_ids = _hex_trace_ids()

        usage = {
            "vendor": vendor,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "method": method,
            "path": path,
            "user_id": user_id,
            "request_id": req_id,
            **trace_ids,
        }
        if metadata:
            usage["metadata"] = metadata

        # Store in context to enrich the final access log
        try:
            token_usage_var.set({
                "model": model,
                "vendor": vendor,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd,
            })
        except Exception:
            pass

        logger.info("token_usage", extra={"event": "token_usage", "usage": usage, "request_id": req_id})

        # Emit as OTEL event on the current span
        event_attrs = {k: str(v) for k, v in usage.items() if v is not None}
        log_custom_event("token_usage", event_attrs)
    except Exception:
        # Never fail app flow due to logging
        pass



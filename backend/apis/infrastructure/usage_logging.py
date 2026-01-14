import logging
from typing import Optional, Dict, Any

from ..core.request_context import token_usage_var

logger = logging.getLogger("apis.app")


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
    """Log AI token usage for cost tracking and monitoring.
    
    OpenTelemetry automatically captures request context and tracing.
    This function focuses on token usage tracking only.
    """
    try:
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)

        usage = {
            "vendor": vendor,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
        }
        if metadata:
            usage["metadata"] = metadata

        # Store in context for middleware to include in access logs
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

        # Simple log entry - OpenTelemetry captures the rest
        logger.info(f"Token usage: {vendor}/{model} - {total_tokens} tokens", extra={"token_usage": usage})

    except Exception:
        # Never fail app flow due to logging
        pass
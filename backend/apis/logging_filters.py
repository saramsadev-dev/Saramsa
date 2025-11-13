import logging
from typing import Iterable


SENSITIVE_HEADERS: Iterable[str] = (
    'authorization', 'cookie', 'set-cookie', 'x-api-key', 'x-auth-token'
)
SENSITIVE_FIELDS: Iterable[str] = (
    'password', 'pass', 'token', 'access_token', 'refresh_token', 'secret',
)


class TraceContextFilter(logging.Filter):
    """Injects OpenTelemetry trace/span IDs into log records when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            context = span.get_span_context() if span else None
            if context and context.is_valid:
                record.trace_id = format(context.trace_id, '032x')
                record.span_id = format(context.span_id, '016x')
        except Exception:
            # Do not fail logging if OTEL unavailable
            pass
        return True


def redact_headers(headers: dict) -> dict:
    if not isinstance(headers, dict):
        return headers
    redacted = {}
    for k, v in headers.items():
        if isinstance(k, str) and k.lower() in SENSITIVE_HEADERS:
            redacted[k] = 'REDACTED'
        else:
            redacted[k] = v
    return redacted


def redact_payload(payload: dict | str | bytes) -> dict | str:
    try:
        if isinstance(payload, dict):
            redacted = {}
            for k, v in payload.items():
                if isinstance(k, str) and k.lower() in SENSITIVE_FIELDS:
                    redacted[k] = 'REDACTED'
                else:
                    redacted[k] = v
            return redacted
        return payload
    except Exception:
        return payload



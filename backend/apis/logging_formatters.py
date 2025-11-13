import json
import logging
import os
from datetime import datetime, timezone


DEFAULT_FIELDS = {
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module',
    'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs',
    'relativeCreated', 'thread', 'threadName', 'processName', 'process',
}


class JsonFormatter(logging.Formatter):
    """JSON log formatter with trace correlation and environment metadata."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

    def format(self, record: logging.LogRecord) -> str:
        def _safe(value):
            # Recursively coerce to JSON-serializable primitives
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, (list, tuple)):
                return [_safe(v) for v in value]
            if isinstance(value, dict):
                return {str(k): _safe(v) for k, v in value.items()}
            # Fallback to string representation (truncate long ones)
            try:
                s = str(value)
            except Exception:
                s = repr(value)
            return s[:2000]

        log = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': _safe(record.getMessage()),
            'path': record.pathname,
            'line': record.lineno,
            'function': record.funcName,
            'process': record.process,
            'thread': record.thread,
            'service': os.getenv('WEBSITE_SITE_NAME', 'saramsa-backend'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
        }

        # Trace correlation if injected by filter
        trace_id = getattr(record, 'trace_id', None)
        span_id = getattr(record, 'span_id', None)
        if trace_id:
            log['trace_id'] = trace_id
        if span_id:
            log['span_id'] = span_id

        # Include extra attributes
        extras = {}
        for key, value in record.__dict__.items():
            if key not in DEFAULT_FIELDS and key not in ('asctime',):
                # Don't duplicate message
                if key == 'msg' or key == 'message':
                    continue
                # Skip internal logging attrs starting with underscore
                if key.startswith('_'):
                    continue
                # Place known structured keys at top-level
                if key in ('event', 'http', 'user', 'exception'):
                    log[key] = _safe(value)
                else:
                    extras[key] = _safe(value)

        if extras:
            log['extra'] = extras

        return json.dumps(log, ensure_ascii=False)



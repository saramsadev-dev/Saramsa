import requests
from typing import Any, Dict, Optional

from .request_context import request_id_var


def _inject_request_id(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    merged = dict(headers or {})
    try:
        req_id = request_id_var.get()
    except Exception:
        req_id = None
    if req_id and 'X-Request-ID' not in {k.title(): v for k, v in merged.items()}:
        merged['X-Request-ID'] = req_id
    return merged


def patch_requests_propagation() -> None:
    """Monkeypatch requests to propagate X-Request-ID on all outbound calls."""
    orig = requests.sessions.Session.request

    def wrapped(self, method: str, url: str, *args: Any, **kwargs: Any):
        try:
            kwargs['headers'] = _inject_request_id(kwargs.get('headers'))
        except Exception:
            pass
        return orig(self, method, url, *args, **kwargs)

    # Avoid double patch
    if getattr(requests.sessions.Session.request, "_x_request_id_patched", False):
        return
    wrapped._x_request_id_patched = True  # type: ignore[attr-defined]
    requests.sessions.Session.request = wrapped  # type: ignore[assignment]



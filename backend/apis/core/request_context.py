import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
token_usage_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar('token_usage', default=None)
import contextvars


# Holds the current request's correlation id (X-Request-ID)
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

# Holds token usage collected during a request (to enrich access log)
token_usage_var: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "token_usage", default=None
)



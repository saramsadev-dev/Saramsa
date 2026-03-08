import hashlib
import json
import os
import sys
import urllib.request


REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-registry.json")
DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def _load_dotenv(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        return


def _fetch_schema(base_url):
    url = base_url.rstrip("/") + "/api/schema/"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"version": 1, "endpoints": []}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)
        f.write("\n")


SKIP_PREFIXES = [
    "/api/projects/",
    "/insights/",
]

SKIP_ENDPOINTS = {
    "GET /api/auth/register/",
    "GET /api/integrations/azure/",
    "POST /api/performance/reset/",
    "GET /api/integrations/{project_id}/",
    "DELETE /api/integrations/{project_id}/",
    "GET /api/integrations/{project_id}/analysis/latest/",
    "GET /api/integrations/{project_id}/trends/",
    "GET /api/integrations/{project_id}/trends/aspects/{aspect_key}/",
    "GET /api/integrations/list/",
}

FEEDBACK_INSIGHT_ALIASES = {
    "/api/feedback/analyze/": "/api/insights/analyze/",
    "/api/feedback/task-status/": "/api/insights/task-status/",
    "/api/feedback/tasks/": "/api/insights/tasks/",
    "/api/feedback/comments/": "/api/insights/comments/",
    "/api/feedback/upload/": "/api/insights/upload/",
    "/api/feedback/keywords/update/": "/api/insights/keywords/update/",
    "/api/feedback/insights/": "/api/insights/insights/",
    "/api/feedback/ingestion/": "/api/insights/ingestion/",
}


def _is_redundant(method, path):
    key = f"{method.upper()} {path}"
    if key in SKIP_ENDPOINTS:
        return True
    if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    for feedback_prefix in FEEDBACK_INSIGHT_ALIASES:
        if path.startswith(feedback_prefix):
            return True
    return False


def _endpoint_key(method, path):
    return f"{method.upper()} {path}"


def _schema_hash(meta):
    """Deterministic hash of a Swagger operation definition.

    Captures parameters, request body, responses, and security so any
    change to the endpoint contract is detected.
    """
    sig = {
        "parameters": meta.get("parameters"),
        "requestBody": meta.get("requestBody"),
        "responses": meta.get("responses"),
        "security": meta.get("security"),
    }
    canonical = json.dumps(sig, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def main():
    _load_dotenv(DOTENV_PATH)
    base_url = os.getenv("API_BASE_URL") or "http://127.0.0.1:8000"
    schema = _fetch_schema(base_url)
    registry = _load_registry()

    existing = {}
    for ep in registry.get("endpoints", []):
        key = _endpoint_key(ep.get("method", "GET"), ep.get("path", ""))
        existing[key] = ep

    updated = []
    new_endpoints = []
    changed_endpoints = []

    paths = schema.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, meta in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            if _is_redundant(method, path):
                continue
            key = _endpoint_key(method, path)
            current_hash = _schema_hash(meta)

            if key in existing:
                ep = existing[key]
                prev_hash = ep.get("schema_hash")

                if prev_hash and prev_hash != current_hash:
                    ep["schema_changed"] = True
                    ep["prev_schema_hash"] = prev_hash
                    changed_endpoints.append(ep)

                ep["schema_hash"] = current_hash
                updated.append(ep)
                continue

            name = (meta.get("summary") or meta.get("operationId") or key)
            entry = {
                "name": name,
                "method": method.upper(),
                "path": path,
                "auth": "bearer",
                "enabled": False,
                "expected_status": 200,
                "expect_json_keys": ["data"],
                "source": "swagger",
                "discovered": True,
                "schema_hash": current_hash
            }
            updated.append(entry)
            new_endpoints.append(entry)

    unconfigured = [
        ep for ep in updated
        if ep.get("discovered") and not ep.get("enabled")
    ]

    registry["endpoints"] = updated
    _save_registry(registry)

    has_issues = False

    if new_endpoints:
        print(f"Synced registry from Swagger. {len(new_endpoints)} NEW endpoint(s) added.")
        for ep in new_endpoints:
            print(f"  + {ep['method']} {ep['path']}  ({ep['name']})")

    if changed_endpoints:
        has_issues = True
        print(f"\nWARNING: {len(changed_endpoints)} endpoint(s) have CHANGED their Swagger schema:")
        for ep in changed_endpoints:
            print(f"  ~ {ep['method']} {ep['path']}  ({ep.get('name', '')})")
        print(
            "\nThe API contract changed for the endpoints above. For each one:\n"
            "  1. Check the Django view — did the request/response shape change?\n"
            "  2. Update \"expected_status\", \"expect_json_keys\", and \"body\" in api-registry.json if needed\n"
            "  3. Remove the \"schema_changed\" flag once verified\n"
        )

    if unconfigured:
        has_issues = True
        print(f"\nERROR: {len(unconfigured)} endpoint(s) need test configuration in api-registry.json:")
        for ep in unconfigured:
            print(f"  - {ep['method']} {ep['path']}  ({ep['name']})")
        print(
            "\nFor each endpoint above, open api-registry.json and:\n"
            "  1. Set \"enabled\": true\n"
            "  2. Set the correct \"expected_status\" (e.g. 200, 201, 204)\n"
            "  3. Set \"expect_json_keys\" to match the actual response shape\n"
            "  4. Add a \"body\" object if the method requires a request body\n"
            "  5. Remove the \"discovered\": true flag once configured\n"
        )

    if has_issues:
        return 1

    print("Synced registry from Swagger. All endpoints configured, no schema changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""One-time script to bulk-configure api-registry.json endpoints.

Reads the current registry, applies sensible defaults based on endpoint
patterns, and writes it back. Run once, then fine-tune manually if needed.
"""

import json
import os
import re

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-registry.json")

NO_AUTH_PATHS = {
    "/api/auth/login/",
    "/api/auth/register/",
    "/api/auth/register/request-otp/",
    "/api/auth/token/",
    "/api/auth/token/refresh/",
    "/api/auth/refresh/",
    "/api/auth/forgot-password/",
    "/api/auth/reset-password/",
    "/api/auth/check-username",
    "/api/health/",
    "/api/performance/",
}

HAS_PATH_PARAM = re.compile(r"\{([^}]+)\}")

BODY_TEMPLATES = {
    "POST /api/auth/login/": {"email": "{{LOGIN_EMAIL}}", "password": "{{LOGIN_PASSWORD}}"},
    "POST /api/auth/register/": {"email": "test_register@example.com", "username": "test_reg_user", "password": "TestPass123!"},
    "POST /api/auth/register/request-otp/": {"email": "test_register@example.com"},
    "POST /api/auth/token/": {"email": "{{LOGIN_EMAIL}}", "password": "{{LOGIN_PASSWORD}}"},
    "POST /api/auth/token/refresh/": None,
    "POST /api/auth/forgot-password/": {"email": "test@example.com"},
    "POST /api/auth/reset-password/": None,
}

SKIP_METHODS = {"DELETE"}

EXPECTED_STATUS_OVERRIDES = {
    "POST /api/auth/register/": 201,
    "POST /api/auth/register/request-otp/": 200,
    "POST /api/auth/forgot-password/": 200,
}

ALWAYS_SKIP = {
    "POST /api/auth/reset-password/",
    "POST /api/auth/token/refresh/",
    "POST /api/auth/refresh/",
    "POST /api/performance/reset/",
}


def configure():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    endpoints = registry.get("endpoints", [])
    enabled_count = 0
    skipped_count = 0

    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path = ep.get("path", "")
        key = f"{method} {path}"

        if key in ALWAYS_SKIP:
            ep["enabled"] = False
            ep.pop("discovered", None)
            ep.pop("source", None)
            skipped_count += 1
            continue

        if method in SKIP_METHODS:
            ep["enabled"] = False
            ep.pop("discovered", None)
            ep.pop("source", None)
            skipped_count += 1
            continue

        has_param = bool(HAS_PATH_PARAM.search(path))
        if has_param:
            only_project_id = all(
                p in ("project_id",) for p in HAS_PATH_PARAM.findall(path)
            )
            if only_project_id:
                ep["enabled"] = True
            else:
                ep["enabled"] = False
                skipped_count += 1
                ep.pop("discovered", None)
                ep.pop("source", None)
                continue

        if path in NO_AUTH_PATHS:
            ep["auth"] = "none"
        else:
            ep["auth"] = "bearer"

        if key in EXPECTED_STATUS_OVERRIDES:
            ep["expected_status"] = EXPECTED_STATUS_OVERRIDES[key]

        if key in BODY_TEMPLATES:
            body = BODY_TEMPLATES[key]
            if body is None:
                ep["enabled"] = False
                skipped_count += 1
                ep.pop("discovered", None)
                ep.pop("source", None)
                continue
            ep["body"] = body

        if not has_param:
            ep["enabled"] = True

        ep["expect_json_keys"] = ["data"]
        ep.pop("discovered", None)
        ep.pop("source", None)
        enabled_count += 1

    registry["endpoints"] = endpoints
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=False)
        f.write("\n")

    total = len(endpoints)
    print(f"Configured {total} endpoints: {enabled_count} enabled, {skipped_count} skipped")
    print(f"\nSkipped reasons:")
    print(f"  - DELETE methods (destructive)")
    print(f"  - Endpoints needing tokens/data we can't auto-generate")
    print(f"  - Path params without {{{{PROJECT_ID}}}} placeholder support")


if __name__ == "__main__":
    configure()

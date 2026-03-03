"""Remove duplicate and redundant endpoints from api-registry.json.

Redundancy sources:
1. /api/projects/* is a duplicate of /api/integrations/* (same urls.py included twice)
2. /api/feedback/* is duplicated by /api/insights/* aliases (frontend uses insights)
3. /insights/* (no /api prefix) are legacy aliases
4. GET methods on POST-only endpoints (e.g. GET /api/auth/register/)
"""

import json
import os
import re

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-registry.json")

REDUNDANT_PREFIXES = [
    "/api/projects/",
    "/insights/",
]

FEEDBACK_DUPLICATED_BY_INSIGHTS = {
    "POST /api/feedback/analyze/",
    "GET /api/feedback/task-status/",
    "GET /api/feedback/tasks/",
    "GET /api/feedback/tasks/stream/",
    "GET /api/feedback/comments/",
    "POST /api/feedback/upload/",
    "POST /api/feedback/keywords/update/",
    "GET /api/feedback/insights/",
    "GET /api/feedback/insights/review/",
    "POST /api/feedback/insights/review/update/",
    "GET /api/feedback/insights/rules/",
    "POST /api/feedback/insights/rules/",
    "POST /api/feedback/insights/rules/apply/",
    "GET /api/feedback/insights/user-stories/",
    "GET /api/feedback/insights/user-stories/all/",
    "POST /api/feedback/ingestion/run-now/",
    "GET /api/feedback/ingestion/schedule/",
    "POST /api/feedback/ingestion/schedule/",
}

UNUSED_ENDPOINTS = {
    "GET /api/auth/register/",
    "GET /api/integrations/azure/",
    "POST /api/performance/reset/",
}


def _is_feedback_duplicate(method, path):
    key = f"{method} {path}"
    if key in FEEDBACK_DUPLICATED_BY_INSIGHTS:
        return True
    for dup_key in FEEDBACK_DUPLICATED_BY_INSIGHTS:
        dup_method, dup_path = dup_key.split(" ", 1)
        if method == dup_method and path.startswith(dup_path.rstrip("/")):
            return True
    return False


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    endpoints = registry.get("endpoints", [])
    kept = []
    removed = {"prefix_dup": [], "feedback_dup": [], "unused": []}

    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path = ep.get("path", "")
        key = f"{method} {path}"

        if any(path.startswith(prefix) for prefix in REDUNDANT_PREFIXES):
            removed["prefix_dup"].append(key)
            continue

        if _is_feedback_duplicate(method, path):
            removed["feedback_dup"].append(key)
            continue

        if key in UNUSED_ENDPOINTS:
            removed["unused"].append(key)
            continue

        kept.append(ep)

    registry["endpoints"] = kept
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=False)
        f.write("\n")

    total_removed = sum(len(v) for v in removed.values())
    print(f"Kept {len(kept)} endpoints, removed {total_removed}:\n")
    print(f"  /api/projects/* duplicates (same as /api/integrations/*): {len(removed['prefix_dup'])}")
    for r in removed["prefix_dup"]:
        print(f"    - {r}")
    print(f"\n  /api/feedback/* duplicates (aliased at /api/insights/*): {len(removed['feedback_dup'])}")
    for r in removed["feedback_dup"]:
        print(f"    - {r}")
    print(f"\n  Unused/unreachable endpoints: {len(removed['unused'])}")
    for r in removed["unused"]:
        print(f"    - {r}")


if __name__ == "__main__":
    main()

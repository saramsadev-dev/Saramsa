import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "api-registry.json"


def _json_request(url, method="GET", headers=None, body=None, timeout=30):
    data = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = None
            if raw:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
            return resp.status, parsed, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
        return e.code, parsed, raw
    except urllib.error.URLError as e:
        return 0, None, f"Connection error: {e.reason}"
    except Exception as e:
        return 0, None, f"Request error: {e}"


def _load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("endpoints", [])


def _replace_placeholders(value):
    if isinstance(value, str):
        matches = re.findall(r"\{\{([A-Z0-9_]+)\}\}", value)
        for key in matches:
            value = value.replace(f"{{{{{key}}}}}", os.getenv(key, ""))
        return value
    if isinstance(value, dict):
        return {k: _replace_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(v) for v in value]
    return value


def _fill_path_params(path):
    defaults = {
        "project_id": os.getenv("PROJECT_ID", "test-project-id"),
        "analysis_id": "test-analysis-id",
        "task_id": "test-task-id",
        "work_item_id": "test-work-item-id",
        "user_id": "test-user-id",
        "aspect_key": "test-aspect",
        "platform": "jira",
        "account_id": "test-account-id",
    }
    parts = path.split("/")
    filled = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            name = part[1:-1]
            filled.append(defaults.get(name, f"test-{name}"))
        else:
            filled.append(part)
    return "/".join(filled)


def _resolve_token(base_url):
    token = os.getenv("API_TOKEN", "").strip()
    if token:
        return token

    email = os.getenv("LOGIN_EMAIL", "").strip()
    password = os.getenv("LOGIN_PASSWORD", "").strip()
    if not email or not password:
        return ""

    login_url = base_url.rstrip("/") + "/api/auth/login/"
    status, data, _ = _json_request(
        login_url, method="POST", body={"email": email, "password": password}
    )
    if status not in (200, 201) or not isinstance(data, dict):
        return ""

    payload = data.get("data", {})
    if isinstance(payload, dict):
        return (
            payload.get("access")
            or payload.get("token")
            or payload.get("access_token")
            or ""
        )
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify-slack", action="store_true")
    args = parser.parse_args()
    _ = args  # flag is accepted for compatibility with workflow/pre-push calls.

    base_url = os.getenv("API_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        print("API_BASE_URL is required.")
        return 1

    endpoints = [e for e in _load_registry() if e.get("enabled")]
    token = _resolve_token(base_url)

    failures = []
    passed = 0
    for ep in endpoints:
        method = str(ep.get("method", "GET")).upper()
        path = _fill_path_params(str(ep.get("path", "")))
        url = base_url + path
        auth = ep.get("auth", "none")
        headers = {}
        if auth == "bearer":
            if not token:
                failures.append(f"{method} {path} -> missing API_TOKEN or login credentials")
                continue
            headers["Authorization"] = f"Bearer {token}"

        body = _replace_placeholders(ep.get("body")) if "body" in ep else None
        status, data, raw = _json_request(url, method=method, headers=headers, body=body)

        if status == 0:
            failures.append(f"{method} {path} -> {raw}")
            continue

        expected = ep.get("expected_status", 200)
        expected_set = set(expected) if isinstance(expected, list) else {expected}
        if status not in expected_set:
            failures.append(f"{method} {path} -> status {status}, expected {sorted(expected_set)}")
            continue

        expected_keys = ep.get("expect_json_keys", [])
        if expected_keys:
            if not isinstance(data, dict):
                failures.append(f"{method} {path} -> expected JSON object, got: {raw[:160]}")
                continue
            missing = [k for k in expected_keys if k not in data]
            if missing:
                failures.append(f"{method} {path} -> missing key(s): {', '.join(missing)}")
                continue

        passed += 1

    if failures:
        print(f"API registry test results: {passed} passed, {len(failures)} failed")
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"API registry tests passed for {passed}/{len(endpoints)} enabled endpoint(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

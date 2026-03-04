import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / ".ci_watch_state.json"
OUT_DIR = ROOT / "ai_failures"

WORKFLOWS_TO_WATCH = {
    "Saramsa-backend (master)",
    "Saramsa-frontend (master)",
    "Saramsa-celery-gpu (master)",
    "API Registry Tests",
}


def gh_cmd() -> str:
    """
    Resolve the GitHub CLI executable in a Windows-friendly way.

    Prefers PATH, but falls back to the default install location used earlier:
    C:\\Program Files\\GitHub CLI\\gh.exe
    """
    gh = shutil.which("gh")
    if gh:
        return gh
    default = Path("C:/Program Files/GitHub CLI/gh.exe")
    if default.exists():
        return str(default)
    raise RuntimeError(
        "GitHub CLI 'gh' not found. Ensure it is on PATH or installed to "
        "'C:/Program Files/GitHub CLI/gh.exe'."
    )


def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"processed_runs": []}


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def gh_api_runs() -> List[Dict[str, Any]]:
    """Return recent workflow runs for the current repo using gh CLI."""
    cmd = [
        gh_cmd(),
        "run",
        "list",
        "--json",
        "databaseId,workflowName,conclusion,headBranch,headSha",
        "--limit",
        "20",
    ]
    out = subprocess.check_output(cmd, cwd=ROOT, text=True)
    runs = json.loads(out)
    # Normalize to a shape similar to the actions/runs API for downstream code.
    norm: List[Dict[str, Any]] = []
    for r in runs:
        norm.append(
            {
                "id": r.get("databaseId"),
                "name": r.get("workflowName"),
                "conclusion": r.get("conclusion"),
                "head_branch": r.get("headBranch"),
                "head_sha": r.get("headSha"),
            }
        )
    return norm


def download_artifacts(run_id: int) -> Path:
    """Download all artifacts for a run into ai_failures/<run_id>/."""
    target = OUT_DIR / str(run_id)
    target.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [gh_cmd(), "run", "download", str(run_id), "-D", str(target)],
        cwd=ROOT,
    )
    return target


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    state = load_state()
    processed = set(state.get("processed_runs", []))

    print("Watching GitHub Actions runs for failures. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                runs = gh_api_runs()
            except subprocess.CalledProcessError as e:
                print(f"[watch-ci] gh api failed: {e}")
                time.sleep(60)
                continue

            new_processed = False

            for run in runs:
                run_id = run.get("id")
                name = run.get("name")
                conclusion = run.get("conclusion")

                if not run_id or not name:
                    continue

                if name not in WORKFLOWS_TO_WATCH:
                    continue

                if conclusion != "failure":
                    continue

                if run_id in processed:
                    continue

                print(f"[watch-ci] Found failed run {run_id} for workflow '{name}'")
                try:
                    path = download_artifacts(run_id)
                except subprocess.CalledProcessError as e:
                    print(f"[watch-ci] Failed to download artifacts for run {run_id}: {e}")
                    continue

                print(
                    f"[watch-ci] Downloaded artifacts for run {run_id} to {path}. "
                    f"Look for 'ai_failure_context.json' there."
                )

                processed.add(run_id)
                new_processed = True

            if new_processed:
                state["processed_runs"] = sorted(processed)
                save_state(state)

            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[watch-ci] Stopped by user.")
        state["processed_runs"] = sorted(processed)
        save_state(state)


if __name__ == "__main__":
    main()


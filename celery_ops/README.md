# Celery Ops

A **Flower-like**, **ops-only** library for observing and lightly controlling Celery task execution. It provides visibility (task lists, states, timelines, worker health) and limited control (best-effort cancel, retry, requeue) via a lightweight API and optional web UI.

**Audience**: Developers and operators only. Not for end users or product features.

See **[SCOPE.md](SCOPE.md)** for the full scope boundary, limitations, and how this differs from workflow platforms like Trigger.dev.

## Install

From the **`celery_ops`** directory (project root):

```bash
cd celery_ops
pip install -e .
```

If you use a venv inside `backend` (e.g. Django), install from the repo root:

```bash
cd "E:\D drive\Desktop\Saramsa"   # or your repo root
pip install -e ./celery_ops
```

Use the **same venv** as your Celery app (Django, etc.).

## Run

Activate your venv, then attach to your Celery app:

```bash
celery-ops serve -A apis
# or: celery-ops serve -A apis.infrastructure.celery:app
```

If `celery-ops` is not found (e.g. on Windows), run as a module:

```bash
python -m celery_ops serve -A apis
```

Options:

- `--host`, `--port`: API/UI server bind (default `0.0.0.0:9800`).
- `--no-ui`: Serve API only, no web UI.
- `--store`: `memory` (default) | `sqlite` | `redis` — optional best-effort persistence for ops history. Data is disposable.

## API

- `GET /api/tasks` — List tasks (optional filters: `state`, `task_name`, `worker`).
- `GET /api/tasks/{task_id}` — Task detail (metadata, runtime, traceback when available).
- `POST /api/tasks/{task_id}/cancel` — Best-effort cancel (revoke + cooperative). **Non-guaranteed.**
- `POST /api/tasks/{task_id}/retry` — Retry (requeue same arguments). Best-effort.
- `GET /api/workers` — List workers.
- `GET /api/workers/{name}` — Worker detail.
- `GET /api/queues` — List queues (from inspect).

## UI

Optional web UI at `/` (or `--no-ui` to disable). Shows:

- Task list with filters, task detail, execution timelines, retries, failures.
- Worker list and health.
- Basic actions: Cancel, Retry.

The UI is a **visual debugger** for Celery. It does **not** expose business meaning, user-facing job concepts, billing, or guaranteed results.

## Configuration

- **Celery app**: Via `-A` (same as Celery/Flower). Example: `-A apis` or `-A apis.infrastructure.celery:app`.
- **Broker / result backend**: From the Celery app config.
- **Ops server**: `--host`, `--port`, `--no-ui`, `--store`.
- **Events**: Task lifecycle (sent, received, started, succeeded, failed) comes from Celery’s event stream. Ensure workers emit events (default). For `task-sent`, the client must set `task_send_sent_event = True` on the Celery app.

## Limitations

- **Cancel** is cooperative and best-effort; workers must honour revoke.
- **Retry / requeue** use task args/kwargs from events; not all task types may be retriable.
- **Ops metadata** is best-effort, disposable, and non-authoritative. If the library stops or crashes, Celery and the app keep running; ops history may be lost.

## License

See repository license.

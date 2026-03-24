# Saramsa

Saramsa is a full-stack application with a Next.js frontend, Django backend, Celery workers, and a Celery Ops dashboard.

## Prerequisites

- **Node.js** and **npm**
- **Python 3** with a virtual environment at `backend/venv/`
- **Redis** (Windows native or WSL)
- **honcho** (`pip install honcho` in the backend venv)
- **Neon PostgreSQL** database (configured via `DATABASE_URL` in `backend/.env`)

## First-Time Setup (PATH)

Each developer needs to run this **once** so the `saramsa` command works from any terminal:

```
setup-path.bat
```

This adds the repo root to your user PATH. **Open a new terminal** after running it.

> If you prefer to do it manually: add the repo root directory (where `saramsa.bat` lives) to your user PATH environment variable.

## Commands

| Command                      | Description                                      |
|------------------------------|--------------------------------------------------|
| `saramsa start`              | Start all services (frontend, backend, celery, celery-ops) |
| `saramsa kill`               | Stop all Saramsa services on ports 8000/3001/9800 |
| `saramsa log <service> -f`   | Follow logs for a service                        |
| `saramsa help`               | Show usage help                                  |

### Log targets

```
saramsa log frontend -f
saramsa log backend -f
saramsa log celery -f
saramsa log celery-ops -f
saramsa log system -f
saramsa log all -f
```

## Services

| Service      | URL                         |
|--------------|-----------------------------|
| Frontend     | http://localhost:3001        |
| Backend      | http://127.0.0.1:8000       |
| Celery Ops   | http://localhost:9800        |
| Redis        | localhost:6379               |

## How It Works

- `saramsa.bat` calls `saramsa.ps1`, which delegates to scripts in `saramsa-scripts/`.
- `saramsa start` uses **honcho** to run all services defined in the `Procfile` in the foreground.
- Press **Ctrl+C** to stop all services.
- Logs are written to `.saramsa-*.log` files in the repo root.

## Project Structure

```
Saramsa/
├── saramsa.bat              # CLI entry point
├── saramsa.ps1              # PowerShell dispatcher
├── setup-path.bat           # One-time PATH setup for developers
├── Procfile                 # Service definitions for honcho
├── saramsa-scripts/         # Start, kill, log, help scripts
├── saramsa-ai/              # Next.js frontend
├── backend/                 # Django backend + Celery
│   └── venv/                # Python virtual environment
└── celery_ops/              # Celery Ops dashboard
```

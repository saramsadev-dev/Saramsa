# Saramsa Service Manager

Master CLI (`saramsa.ps1`) that invokes child scripts in `saramsa-scripts/` to start, stop, and tail logs for all services.

## Script layout

- **`saramsa.ps1`** – Master CLI: parses `start` / `logs` / `kill` / `help` and invokes child scripts
- **`saramsa-scripts/common.ps1`** – Shared paths, Redis checks, PID helpers, `Stop-AllServices`
- **`saramsa-scripts/start.ps1`** – Start Redis, Backend, Celery, Celery Ops, Frontend; prints URLs + Logs section
- **`saramsa-scripts/logs.ps1`** – Tail a service log or show log paths + `Get-Content` commands
- **`saramsa-scripts/kill.ps1`** – Stop all services
- **`saramsa-scripts/help.ps1`** – Print usage

## Quick Start

### Option 1: Direct PowerShell Script

```powershell
# From project root
.\saramsa.ps1 start all dev
.\saramsa.ps1 logs          # Show log paths and tail commands
.\saramsa.ps1 logs backend  # Tail backend log
.\saramsa.ps1 kill
```

### Option 2: Batch File

```cmd
saramsa.bat start all dev
saramsa.bat logs [backend|frontend|celery|celery-ops]
saramsa.bat kill
```

### Option 3: PowerShell function (one-time setup)

```powershell
.\setup-saramsa-command.ps1
. $PROFILE

saramsa start all dev
saramsa logs [backend|frontend|celery|celery-ops]
saramsa kill
```

## Commands

- **`saramsa start all [dev|prod]`** – Start all services (Redis, Backend, Celery, Celery Ops, Frontend). Prints Service URLs and **Logs** (paths + `Get-Content ... -Wait -Tail 50`).
- **`saramsa logs`** – Show log paths and tail commands only
- **`saramsa logs [backend|frontend|celery|celery-ops]`** – Tail that service’s log
- **`saramsa kill`** (alias: **`stop`**) – Stop all services
- **`saramsa help`** – Show usage

## Services Started

1. **Frontend (Next.js)** - http://localhost:3000
2. **Backend (Django)** - http://127.0.0.1:8000
3. **Celery Worker** - Background task processing
4. **Celery Ops (Monitoring UI)** - http://localhost:9800

Each service runs in a separate PowerShell window. Close individual windows to stop specific services.

## Prerequisites

- **Python 3.11+** with virtual environment in `backend/venv`
- **Node.js 18+** and npm
- **Redis** running (for Celery broker)

## Troubleshooting

### Virtual Environment Not Found

If you see a warning about venv, make sure:
1. Virtual environment exists at `backend/venv`
2. Or install dependencies globally (not recommended)

### Port Already in Use

If a port is already in use:
- **3000**: Frontend - Stop other Next.js apps
- **8000**: Backend - Stop other Django servers
- **9800**: Celery Ops - Stop other instances

### Services Not Starting

1. Check that all dependencies are installed:
   ```powershell
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd saramsa-ai
   npm install
   ```

2. Ensure Redis is running:
   ```powershell
   # Check Redis
   redis-cli ping
   ```

3. Check individual service logs in their respective windows

### Redis failed to start / "Redis failed to start. Start manually"

If `saramsa start all dev` shows **"Redis failed to start"** and suggests WSL commands:

- **Option A – Redis on Windows (recommended when running backend on Windows)**  
  So the backend (and Celery) can connect to `localhost:6379` without WSL networking:

  1. Install Redis for Windows (PowerShell as Administrator):
     ```powershell
     choco install redis-64 -y
     ```
     Or download from: [tporadowski/redis/releases](https://github.com/tporadowski/redis/releases)

  2. Start Redis (pick one):
     - If installed as a service: start the **Redis** service from Services (services.msc), or:
       ```powershell
       Start-Service Redis
       ```
     - Or run in a terminal: `redis-server`

  3. Verify from project root:
     ```powershell
     redis-cli ping
     ```
     Should return `PONG`. Then run `.\saramsa.ps1 start all dev` again (or start only backend/Celery if the rest are already running).

- **Option B – Redis in WSL**  
  If you prefer WSL:

  1. Install and start Redis inside WSL:
     ```bash
     wsl
     sudo apt-get update && sudo apt-get install -y redis-server
     redis-server --daemonize yes
     redis-cli ping
     exit
     ```

  2. From PowerShell, check:
     ```powershell
     wsl redis-cli ping
     ```
     If that returns `PONG` but the backend still cannot connect, WSL2 may not be exposing port 6379 to Windows. Use Option A (Redis on Windows) instead.

### 500 Error on Analyze / "Error 10061 connecting to localhost:6379"

If `POST /api/insights/analyze/` returns **500** with a message like *"Error 10061 connecting to localhost:6379"* or *"target machine actively refused it"*:

- **Cause:** Redis is not running. The analyze endpoint enqueues a Celery task, and Celery uses Redis as the broker.
- **Fix:**
  1. Start Redis, then start the Celery worker. Easiest: from project root run **`.\saramsa.ps1 start all dev`** (it starts Redis, backend, Celery, Celery Ops, frontend).
  2. If you start services manually, start **Redis first** (e.g. `redis-server` or WSL: `wsl redis-server --daemonize yes`), then backend and Celery.
  3. Verify Redis: `redis-cli ping` should return `PONG`.
- **Logs:** The backend logs this as an error. Use `saramsa logs backend` and check `.saramsa-backend.err.log` in the project root.

## Manual Start (Alternative)

If the script doesn't work, start services manually:

```powershell
# Terminal 1: Backend
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2: Celery Worker
cd backend
.\venv\Scripts\Activate.ps1
celery -A apis worker -l info

# Terminal 3: Celery Ops
cd backend
.\venv\Scripts\Activate.ps1
python -m celery_ops serve -A apis

# Terminal 4: Frontend
cd saramsa-ai
npm run dev
```

# Saramsa Service Manager

Master CLI (`saramsa.ps1`) that invokes child scripts in `saramsa-scripts/` to start services.

## Script layout

- **`saramsa.ps1`** - Master CLI: parses `start` / `kill` / `help` and invokes child scripts
- **`saramsa-scripts/common.ps1`** - Shared paths, Redis checks, and startup helpers
- **`saramsa-scripts/start-procfile.ps1`** - Start via Procfile + honcho (foreground)
- **`saramsa-scripts/kill.ps1`** - Stop Saramsa processes by their bound ports
- **`saramsa-scripts/help.ps1`** - Print usage

## Quick Start

### Option 1: Procfile + honcho (recommended)

```powershell
pip install honcho
.\saramsa.ps1 start
```

### Option 2: PowerShell function (one-time setup)

```powershell
.\setup-saramsa-command.ps1
. $PROFILE

saramsa start
```

## Commands

- **`saramsa start`** - Start all services via Procfile + honcho (foreground)
- **`saramsa kill`** - Stop Saramsa services using ports `8000`, `3001`, and `9800`
- **`saramsa help`** - Show usage

## Services Started

1. **Frontend (Next.js)** - http://localhost:3001
2. **Backend (Django)** - http://127.0.0.1:8000
3. **Celery Worker** - Background task processing
4. **Celery Ops (Monitoring UI)** - http://localhost:9800

Procfile mode runs all services in a single foreground session. Press Ctrl+C to stop all services.

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
- **3001**: Frontend - Stop other Next.js apps
- **8000**: Backend - Stop other Django servers
- **9800**: Celery Ops - Stop other instances

If the existing listeners are from Saramsa itself, run:

```powershell
saramsa kill
```

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
   redis-cli ping
   ```

3. Check the terminal output from honcho
4. Runtime logs are written under `saramsa-logs/runtime/`

### Redis failed to start / "Redis failed to start. Start manually"

If `saramsa start` shows **"Redis failed to start"** and suggests WSL commands:

- **Option A - Redis on Windows (recommended when running backend on Windows)**
  So the backend (and Celery) can connect to `localhost:6379` without WSL networking:

  1. Install Redis for Windows (PowerShell as Administrator):
     ```powershell
     choco install redis-64 -y
     ```
     Or download from: [tporadowski/redis/releases](https://github.com/tporadowski/redis/releases)

  2. Start Redis (pick one):
     - If installed as a service: start the **Redis** service from Services (`services.msc`), or:
       ```powershell
       Start-Service Redis
       ```
     - Or run in a terminal: `redis-server`

  3. Verify from project root:
     ```powershell
     redis-cli ping
     ```
     Should return `PONG`. Then run `.\saramsa.ps1 start` again.

- **Option B - Redis in WSL**
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
     If that returns `PONG` but the backend still cannot connect, WSL2 may not be exposing port 6379 to Windows. Use Option A instead.

### 500 Error on Analyze / "Error 10061 connecting to localhost:6379"

If `POST /api/insights/analyze/` returns **500** with a message like *"Error 10061 connecting to localhost:6379"* or *"target machine actively refused it"*:

- **Cause:** Redis is not running. The analyze endpoint enqueues a Celery task, and Celery uses Redis as the broker.
- **Fix:**
  1. Start Redis, then run **`.\saramsa.ps1 start`**.
  2. If you start services manually, start **Redis first** (for example `redis-server` or `wsl redis-server --daemonize yes`), then backend and Celery.
  3. Verify Redis: `redis-cli ping` should return `PONG`.
- **Logs:** The backend logs this as an error in the terminal output.

## Manual Start (Alternative)

If the script does not work, start services manually:

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

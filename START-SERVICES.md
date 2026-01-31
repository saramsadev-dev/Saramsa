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

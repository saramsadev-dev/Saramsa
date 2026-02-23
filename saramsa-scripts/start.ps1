# Saramsa start - start all services
# Invoked by master saramsa.ps1: & start.ps1 -Env dev

param([string]$Env = "dev")

. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $VenvActivate)) {
    Write-Host "[WARNING] venv not found: $VenvPath. Using system Python." -ForegroundColor Yellow
}

function Start-Backend {
    Write-Host "Starting Django Backend..." -ForegroundColor Cyan
    if ($UseVenv -and (Test-Path $VenvActivate)) {
        $script = @"
Set-Location '$BackendDir'
& '$VenvActivate'
python -u manage.py runserver 127.0.0.1:8000
"@
        $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
        $script | Out-File -FilePath $tmp -Encoding UTF8
        $psi = @{
            FilePath               = "powershell"
            ArgumentList           = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $tmp)
            WorkingDirectory       = $BackendDir
            RedirectStandardOutput = $BackendLog
            RedirectStandardError  = $BackendErrLog
            PassThru               = $true
            WindowStyle            = "Hidden"
        }
        $p = Start-Process @psi
    } else {
        $psi = @{
            FilePath               = "python"
            ArgumentList           = @("-u", "manage.py", "runserver", "127.0.0.1:8000")
            WorkingDirectory       = $BackendDir
            RedirectStandardOutput = $BackendLog
            RedirectStandardError  = $BackendErrLog
            PassThru               = $true
            WindowStyle            = "Hidden"
        }
        $p = Start-Process @psi
    }
    Save-ProcessId "backend" $p.Id
    Start-Sleep -Seconds 2
}

function Start-Celery {
    Write-Host "Starting Celery Worker..." -ForegroundColor Cyan
    if ($UseVenv -and (Test-Path $VenvActivate)) {
        $script = @"
& '$VenvActivate'
python -u -m celery -A apis worker -l info
"@
        $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
        $script | Out-File -FilePath $tmp -Encoding UTF8
        $psi = @{
            FilePath               = "powershell"
            ArgumentList           = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $tmp)
            WorkingDirectory       = $BackendDir
            RedirectStandardOutput = $CeleryLog
            RedirectStandardError  = $CeleryErrLog
            PassThru               = $true
            WindowStyle            = "Hidden"
        }
        $p = Start-Process @psi
    } else {
        $psi = @{
            FilePath               = "python"
            ArgumentList           = @("-u", "-m", "celery", "-A", "apis", "worker", "-l", "info")
            WorkingDirectory       = $BackendDir
            RedirectStandardOutput = $CeleryLog
            RedirectStandardError  = $CeleryErrLog
            PassThru               = $true
            WindowStyle            = "Hidden"
        }
        $p = Start-Process @psi
    }
    Save-ProcessId "celery" $p.Id
    Start-Sleep -Seconds 2
}

function Start-CeleryOps {
    Write-Host "Starting Celery Ops (API + UI)..." -ForegroundColor Cyan
    
    # Check if React UI directory exists and build it
    if (Test-Path $CeleryOpsUIDir) {
        Write-Host "Building Celery Ops React UI..." -ForegroundColor Yellow
        
        # Check if node_modules exists, if not install dependencies
        $nodeModules = Join-Path $CeleryOpsUIDir "node_modules"
        if (-not (Test-Path $nodeModules)) {
            Write-Host "Installing React UI dependencies..." -ForegroundColor Yellow
            $installScript = @"
Set-Location '$CeleryOpsUIDir'
"Installing dependencies at `$(Get-Date)" | Out-File -FilePath '$CeleryOpsLog' -Append -Encoding utf8
cmd /c "npm install 2>&1" | Out-File -FilePath '$CeleryOpsLog' -Append -Encoding utf8
"@
            $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
            $installScript | Out-File -FilePath $tmp -Encoding UTF8
            $installProcess = Start-Process powershell -ArgumentList "-WindowStyle", "Hidden", "-File", $tmp -PassThru -WindowStyle Hidden -Wait
            if ($installProcess.ExitCode -ne 0) {
                Write-Host "[WARNING] Failed to install React UI dependencies. Will serve API only." -ForegroundColor Yellow
            }
        }
        
        # Build React app for production
        $buildDir = Join-Path $CeleryOpsUIDir "build"
        if (-not (Test-Path $buildDir) -or (Get-ChildItem $buildDir -ErrorAction SilentlyContinue).Count -eq 0) {
            Write-Host "Building React UI for production..." -ForegroundColor Yellow
            $buildScript = @"
Set-Location '$CeleryOpsUIDir'
"Building React UI at `$(Get-Date)" | Out-File -FilePath '$CeleryOpsLog' -Append -Encoding utf8
cmd /c "npm run build 2>&1" | Out-File -FilePath '$CeleryOpsLog' -Append -Encoding utf8
"@
            $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
            $buildScript | Out-File -FilePath $tmp -Encoding UTF8
            $buildProcess = Start-Process powershell -ArgumentList "-WindowStyle", "Hidden", "-File", $tmp -PassThru -WindowStyle Hidden -Wait
            if ($buildProcess.ExitCode -ne 0) {
                Write-Host "[WARNING] Failed to build React UI. Will serve API only." -ForegroundColor Yellow
            } else {
                Write-Host "[OK] React UI built successfully" -ForegroundColor Green
            }
        } else {
            Write-Host "[OK] React UI build already exists" -ForegroundColor Green
        }
    } else {
        Write-Host "[WARNING] React UI directory not found. Will serve API only." -ForegroundColor Yellow
    }
    
    # Start Celery Ops server (API + UI)
    $pyExe = if ($UseVenv -and (Test-Path $VenvActivate)) { "$VenvPath\Scripts\python.exe" } else { "python" }
    $psi = @{
        FilePath               = $pyExe
        ArgumentList           = @("-u", "-m", "celery_ops", "serve", "-A", "apis", "--host", "0.0.0.0", "--port", "9800")
        WorkingDirectory       = $BackendDir
        RedirectStandardOutput = $CeleryOpsLog
        RedirectStandardError  = $CeleryOpsErrLog
        PassThru               = $true
        WindowStyle            = "Hidden"
    }
    $p = Start-Process @psi
    Save-ProcessId "celery-ops" $p.Id
    Start-Sleep -Seconds 2
}

function Start-Frontend {
    Write-Host "Starting Next.js Frontend..." -ForegroundColor Cyan
    $s = @"
`$ErrorActionPreference = 'Continue'
Set-Location '$FrontendDir'
"Frontend starting at `$(Get-Date)" | Out-File -FilePath '$FrontendLog' -Encoding utf8
cmd /c "npm run dev 2>&1" | Out-File -FilePath '$FrontendLog' -Append -Encoding utf8
"@
    $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
    $s | Out-File -FilePath $tmp -Encoding UTF8
    $p = Start-Process powershell -ArgumentList "-WindowStyle", "Hidden", "-File", $tmp -PassThru -WindowStyle Hidden
    Save-ProcessId "frontend" $p.Id
    Start-Sleep -Seconds 2
}

function Show-LogsHelp {
    Write-Host "Logs:" -ForegroundColor Yellow
    Write-Host "   All:         saramsa logs all   # tail all services in one stream" -ForegroundColor White
    Write-Host "   Backend:     Get-Content '$BackendLog','$BackendErrLog' -Wait -Tail 50" -ForegroundColor White
    Write-Host "   Frontend:    Get-Content '$FrontendLog' -Wait -Tail 50" -ForegroundColor White
    Write-Host "   Celery:      Get-Content '$CeleryErrLog' -Wait -Tail 50   # task/app logs; startup: $CeleryLog" -ForegroundColor White
    Write-Host "   Celery Ops:  Get-Content '$CeleryOpsLog','$CeleryOpsErrLog' -Wait -Tail 50   # API + UI" -ForegroundColor White
}

try {
    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Magenta
    Write-Host "  Starting Saramsa Services (Environment: $Env)" -ForegroundColor Magenta
    Write-Host "=======================================================" -ForegroundColor Magenta
    Write-Host ""

    if (-not (Test-Path $FrontendDir)) { Write-Host "[ERROR] Frontend not found: $FrontendDir" -ForegroundColor Red; exit 1 }
    if (-not (Test-Path $BackendDir)) { Write-Host "[ERROR] Backend not found: $BackendDir" -ForegroundColor Red; exit 1 }

    $p8000 = Test-PortListening -Port 8000
    $p3001 = Test-PortListening -Port 3001
    $p9800 = Test-PortListening -Port 9800
    if ($p8000 -or $p3001 -or $p9800) {
        Write-Host "[ERROR] Services already running (ports 8000, 3001, or 9800 in use)." -ForegroundColor Red
        Write-Host "  Run 'saramsa kill' first, then 'saramsa start all dev' to restart." -ForegroundColor Yellow
        exit 1
    }

    try { $nv = node --version 2>$null; $npm = npm --version 2>$null; if ($nv -and $npm) { Write-Host "[OK] Node.js $nv, npm $npm" -ForegroundColor Green } } catch { Write-Host "[WARNING] Node/npm not found. Frontend may not start." -ForegroundColor Yellow }
    try { $pv = python --version 2>&1; if ($pv) { Write-Host "[OK] $pv" -ForegroundColor Green } } catch { Write-Host "[WARNING] Python not found. Backend may not start." -ForegroundColor Yellow }

    Start-Redis
    Start-Backend
    Start-Celery
    Start-CeleryOps
    Start-Frontend

    if (Test-Path $PidFile) {
        Write-Host "PIDs saved to $PidFile" -ForegroundColor Gray
    } else {
        Write-Host "[WARNING] PID file not created. 'saramsa kill' may not stop services." -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Verifying services (waiting for startup)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10

    $any = $false
    if (-not (Test-PortListening -Port 3001)) { Write-Host "[WARNING] Frontend may have failed. Check .saramsa-frontend.log" -ForegroundColor Yellow; $any = $true }
    if (-not (Test-PortListening -Port 8000)) { Write-Host "[WARNING] Backend may have failed. Check .saramsa-backend.log" -ForegroundColor Yellow; $any = $true }
    if (-not (Test-PortListening -Port 9800)) { Write-Host "[WARNING] Celery Ops may have failed. Check .saramsa-celery-ops.log" -ForegroundColor Yellow; $any = $true }
    if ($any) { Write-Host "" }

    Write-Host "[OK] All services started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor Yellow
    Write-Host "   Redis:       localhost:6379" -ForegroundColor White
    Write-Host "   Frontend:    http://localhost:3001" -ForegroundColor White
    Write-Host "   Backend:     http://127.0.0.1:8000" -ForegroundColor White
    Write-Host "   Celery Ops:  http://localhost:9800   # API + React UI" -ForegroundColor White
    Write-Host ""
    Show-LogsHelp
    Write-Host ""
    Write-Host "Note: Services run in background. Use 'saramsa kill' or Ctrl+C to stop." -ForegroundColor Cyan
    if ($any) { Write-Host "      Tail logs: saramsa logs [backend|frontend|celery|celery-ops]" -ForegroundColor Gray }
    Write-Host ""
} catch {
    if ($_.Exception.GetType().Name -eq "PipelineStoppedException" -or $_.Exception.GetType().Name -eq "OperationCanceledException") {
        Write-Host "`n[INFO] Interrupted. Stopping all services..." -ForegroundColor Yellow
        Stop-AllServices
        exit 0
    }
    throw
}

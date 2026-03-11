# Saramsa start (Procfile + honcho) - start all services in foreground
# Invoked by master saramsa.ps1: & start-procfile.ps1

. "$PSScriptRoot\common.ps1"

$Procfile = Join-Path $ScriptDir "Procfile"
$HonchoRawOutLog = Join-Path $ScriptDir ".saramsa-honcho.raw.out.log"
$HonchoRawErrLog = Join-Path $ScriptDir ".saramsa-honcho.raw.err.log"
$script:FrontendReady = $false
$script:BackendReady = $false
$script:CeleryReady = $false
$script:CeleryOpsReady = $false
$script:StartupSummaryPrinted = $false
$script:StartupFailed = $false
$script:StartupErrorPrinted = $false
$script:StartupFailureReason = ""

function Test-NeonDbPreflight {
    param(
        [string]$PythonExe,
        [int]$Attempts = 5,
        [int]$DelaySeconds = 3
    )

    Write-Host "Checking Neon PostgreSQL connectivity..." -ForegroundColor Yellow
    $script = @'
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
import psycopg2

backend_dir = Path.cwd() / "backend"
load_dotenv(backend_dir / ".env")
database_url = os.getenv("DATABASE_URL", "").strip()
if not database_url:
    print("DATABASE_URL is missing.")
    sys.exit(2)

host = (urlparse(database_url).hostname or "").lower()
if not host.endswith(".neon.tech"):
    print(f"DATABASE_URL host is not Neon: {host or 'missing'}")
    sys.exit(2)

attempts = int(os.getenv("SARAMSA_DB_PREFLIGHT_ATTEMPTS", "5"))
delay = int(os.getenv("SARAMSA_DB_PREFLIGHT_DELAY_SECONDS", "3"))
timeout = int(os.getenv("SARAMSA_DB_CONNECT_TIMEOUT", "12"))

for i in range(1, attempts + 1):
    try:
        conn = psycopg2.connect(database_url, connect_timeout=timeout)
        cur = conn.cursor()
        cur.execute("select 1")
        cur.fetchone()
        cur.close()
        conn.close()
        print("NEON_DB_OK")
        sys.exit(0)
    except Exception as exc:
        print(f"attempt {i}/{attempts}: {type(exc).__name__}: {exc}")
        if i < attempts:
            time.sleep(delay)

sys.exit(1)
'@

    $oldAttempts = $env:SARAMSA_DB_PREFLIGHT_ATTEMPTS
    $oldDelay = $env:SARAMSA_DB_PREFLIGHT_DELAY_SECONDS
    try {
        $env:SARAMSA_DB_PREFLIGHT_ATTEMPTS = [string]$Attempts
        $env:SARAMSA_DB_PREFLIGHT_DELAY_SECONDS = [string]$DelaySeconds
        $output = $script | & $PythonExe - 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Neon DB connection verified" -ForegroundColor Green
            return $true
        }
        Write-Host "[ERROR] Neon DB preflight failed:" -ForegroundColor Red
        foreach ($line in $output) {
            if (-not [string]::IsNullOrWhiteSpace([string]$line)) {
                Write-Host "  $line" -ForegroundColor Yellow
            }
        }
        return $false
    } finally {
        if ($null -eq $oldAttempts) { Remove-Item Env:SARAMSA_DB_PREFLIGHT_ATTEMPTS -ErrorAction SilentlyContinue } else { $env:SARAMSA_DB_PREFLIGHT_ATTEMPTS = $oldAttempts }
        if ($null -eq $oldDelay) { Remove-Item Env:SARAMSA_DB_PREFLIGHT_DELAY_SECONDS -ErrorAction SilentlyContinue } else { $env:SARAMSA_DB_PREFLIGHT_DELAY_SECONDS = $oldDelay }
    }
}

function Show-StartupSummary {
    if ($script:StartupSummaryPrinted) { return }
    Write-Host ""
    Write-Host "[OK] All services started." -ForegroundColor Green
    Write-Host "URLs:" -ForegroundColor Yellow
    Write-Host "  Frontend   http://localhost:3001" -ForegroundColor White
    Write-Host "  Backend    http://127.0.0.1:8000" -ForegroundColor White
    Write-Host "  Celery Ops http://localhost:9800" -ForegroundColor White
    Write-Host ""
    Write-Host "Logs:" -ForegroundColor Yellow
    Write-Host "  saramsa log frontend -f" -ForegroundColor White
    Write-Host "  saramsa log backend -f" -ForegroundColor White
    Write-Host "  saramsa log celery -f" -ForegroundColor White
    Write-Host "  saramsa log celery-ops -f" -ForegroundColor White
    Write-Host "  saramsa log system -f" -ForegroundColor White
    Write-Host "  saramsa log all -f" -ForegroundColor White
    Write-Host ""
    $script:StartupSummaryPrinted = $true
}

function Show-StartupError {
    if ($script:StartupErrorPrinted) { return }
    Write-Host ""
    Write-Host "[ERROR] Startup failed. See logs:" -ForegroundColor Red
    if (-not [string]::IsNullOrWhiteSpace($script:StartupFailureReason)) {
        Write-Host "Reason: $($script:StartupFailureReason)" -ForegroundColor Yellow
    }
    Write-Host "  saramsa log all -f" -ForegroundColor Yellow
    Write-Host "  saramsa log system -f" -ForegroundColor Yellow
    Write-Host ""
    $script:StartupErrorPrinted = $true
}

function Append-LogLine {
    param(
        [string]$Path,
        [string]$Line
    )

    $fs = $null
    $sw = $null
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
        [void]$fs.Seek(0, [System.IO.SeekOrigin]::End)
        $sw = New-Object System.IO.StreamWriter($fs, $utf8NoBom)
        $sw.WriteLine($Line)
        $sw.Flush()
    } catch {
        # Keep services running even if a log write fails transiently.
    } finally {
        if ($sw) { $sw.Dispose() }
        if ($fs) { $fs.Dispose() }
    }
}

function Write-HonchoLine {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) { return }

    Append-LogLine -Path $AllLog -Line $Line
    if ($Line -match '^\d{2}:\d{2}:\d{2}\s+([a-zA-Z0-9-]+)\.\d+\s+\|') {
        $procName = $matches[1].ToLowerInvariant()
        switch ($procName) {
            "frontend" { Append-LogLine -Path $FrontendLog -Line $Line }
            "backend" { Append-LogLine -Path $BackendLog -Line $Line }
            "celery" { Append-LogLine -Path $CeleryLog -Line $Line }
            "celery-ops" { Append-LogLine -Path $CeleryOpsLog -Line $Line }
            "system" { Append-LogLine -Path $SystemLog -Line $Line }
        }
    }

    if ($Line -match 'frontend\.1\s+\|.*ready') { $script:FrontendReady = $true }
    if ($Line -match 'backend\.1\s+\|.*starting development server at http://127\.0\.0\.1:8000/') { $script:BackendReady = $true }
    if ($Line -match 'celery\.1\s+\|.*celery@') { $script:CeleryReady = $true }
    if ($Line -match 'celery-ops\.1\s+\|.*uvicorn running on http://0\.0\.0\.0:9800') { $script:CeleryOpsReady = $true }

    if (-not $script:StartupSummaryPrinted -and $Line -match 'system\s+\|.*stopped \(rc=') {
        $script:StartupFailed = $true
        if ([string]::IsNullOrWhiteSpace($script:StartupFailureReason)) {
            $script:StartupFailureReason = "A service exited during startup."
        }
        Show-StartupError
    }

    if (
        -not $script:StartupSummaryPrinted -and
        $Line -match 'backend\.1\s+\|.*(django\.db\.utils\.OperationalError|psycopg2\.OperationalError|could not translate host name|could not connect to server|connection refused|timeout expired|timed out)'
    ) {
        $script:StartupFailed = $true
        $script:StartupFailureReason = "Backend failed to connect to Neon PostgreSQL (DATABASE_URL)."
        Show-StartupError
    }

    if (
        -not $script:StartupSummaryPrinted -and
        $Line -match 'frontend\.1\s+\|.*(EADDRINUSE|address already in use).*3001'
    ) {
        $script:StartupFailed = $true
        $frontendPid = Get-ListeningProcessId -Port 3001
        if ($frontendPid) {
            $script:StartupFailureReason = "Frontend failed to bind port 3001 (already in use by PID $frontendPid)."
        } else {
            $script:StartupFailureReason = "Frontend failed to bind port 3001 (already in use)."
        }
        Show-StartupError
    }

    if (-not $script:StartupSummaryPrinted -and -not $script:StartupFailed -and $script:FrontendReady -and $script:BackendReady -and $script:CeleryReady -and $script:CeleryOpsReady) {
        Show-StartupSummary
    }

    # Keep terminal clean; detailed service output is routed to log files.
}

function Flush-HonchoOutput {
    param(
        [string]$Path,
        [ref]$LineOffset
    )

    if (-not (Test-Path $Path)) { return }

    $lines = $null
    try { $lines = Get-Content -Path $Path -ErrorAction SilentlyContinue } catch { return }
    if (-not $lines) { return }

    for ($i = [int]$LineOffset.Value; $i -lt $lines.Count; $i++) {
        Write-HonchoLine -Line ([string]$lines[$i])
    }
    $LineOffset.Value = $lines.Count
}

try {
    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Magenta
    Write-Host "  Starting Saramsa Services (Procfile + honcho)" -ForegroundColor Magenta
    Write-Host "=======================================================" -ForegroundColor Magenta
    Write-Host ""

    if (-not (Test-Path $Procfile)) {
        Write-Host "[ERROR] Procfile not found: $Procfile" -ForegroundColor Red
        exit 1
    }

    $pythonExe = Get-PythonExe
    try {
        & $pythonExe -m honcho --help *> $null
        if ($LASTEXITCODE -ne 0) { throw "honcho unavailable" }
    } catch {
        Write-Host "[ERROR] honcho not installed in the project Python." -ForegroundColor Red
        Write-Host "Install it with: backend\venv\Scripts\python.exe -m pip install honcho" -ForegroundColor Yellow
        exit 1
    }

    if (-not (Test-Path $FrontendDir)) { Write-Host "[ERROR] Frontend not found: $FrontendDir" -ForegroundColor Red; exit 1 }
    if (-not (Test-Path $BackendDir)) { Write-Host "[ERROR] Backend not found: $BackendDir" -ForegroundColor Red; exit 1 }

    try { $nv = node --version 2>$null; $npm = npm --version 2>$null; if ($nv -and $npm) { Write-Host "[OK] Node.js $nv, npm $npm" -ForegroundColor Green } } catch { Write-Host "[WARNING] Node/npm not found. Frontend may not start." -ForegroundColor Yellow }
    try { $pv = & $pythonExe --version 2>&1; if ($pv) { Write-Host "[OK] $pv" -ForegroundColor Green } } catch { Write-Host "[WARNING] Python not found. Backend may not start." -ForegroundColor Yellow }

    Stop-StaleSaramsaHoncho

    $conflicts = Get-PortConflictSummary
    if ($conflicts.Count -gt 0) {
        Write-Host "[ERROR] Required ports are already in use:" -ForegroundColor Red
        foreach ($conflict in $conflicts) {
            $owner = if ($conflict.IsSaramsa) { "Saramsa" } else { "non-Saramsa" }
            Write-Host "  Port $($conflict.Port): PID $($conflict.ProcessId) ($owner)" -ForegroundColor Yellow
        }
        Write-Host "Run 'saramsa kill' to stop existing Saramsa services, or free the ports manually." -ForegroundColor Yellow
        exit 1
    }

    Start-Redis
    if (-not (Test-NeonDbPreflight -PythonExe $pythonExe -Attempts 5 -DelaySeconds 3)) {
        Write-Host "[ERROR] Aborting startup because Neon DB preflight failed." -ForegroundColor Red
        exit 1
    }

    if (Test-Path $CeleryOpsUIDir) {
        Write-Host "Checking Celery Ops React UI..." -ForegroundColor Yellow
        Rotate-Log $CeleryOpsBuildLog
        Rotate-Log $CeleryOpsBuildErrLog
        $nodeModules = Join-Path $CeleryOpsUIDir "node_modules"
        if (-not (Test-Path $nodeModules)) {
            Write-Host "Installing Celery Ops UI dependencies..." -ForegroundColor Yellow
            $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm install" `
                -WorkingDirectory $CeleryOpsUIDir `
                -RedirectStandardOutput $CeleryOpsBuildLog `
                -RedirectStandardError $CeleryOpsBuildErrLog `
                -PassThru -WindowStyle Hidden -Wait
            if ($installProcess.ExitCode -ne 0) {
                Write-Host "[WARNING] Failed to install Celery Ops UI dependencies. UI may not serve." -ForegroundColor Yellow
            }
        }
        $buildDir = Join-Path $CeleryOpsUIDir "build"
        if (-not (Test-Path $buildDir) -or (Get-ChildItem $buildDir -ErrorAction SilentlyContinue).Count -eq 0) {
            Write-Host "Building Celery Ops UI..." -ForegroundColor Yellow
            $buildProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run build" `
                -WorkingDirectory $CeleryOpsUIDir `
                -RedirectStandardOutput $CeleryOpsBuildLog `
                -RedirectStandardError $CeleryOpsBuildErrLog `
                -PassThru -WindowStyle Hidden -Wait
            if ($buildProcess.ExitCode -ne 0) {
                Write-Host "[WARNING] Failed to build Celery Ops UI. UI may not serve." -ForegroundColor Yellow
            } else {
                Write-Host "[OK] Celery Ops UI built" -ForegroundColor Green
            }
        } else {
            Write-Host "[OK] Celery Ops UI build already exists" -ForegroundColor Green
        }
    }

    Clear-ProcessIds
    foreach ($log in @($FrontendLog, $BackendLog, $CeleryLog, $CeleryOpsLog, $SystemLog, $AllLog)) {
        Rotate-Log $log
    }
    Rotate-Log $HonchoRawOutLog
    Rotate-Log $HonchoRawErrLog

    Write-Host ""
    Write-Host "Starting services in the foreground (Ctrl+C stops all)..." -ForegroundColor Cyan
    Write-Host "Writing split logs to .saramsa-*.log files in repo root..." -ForegroundColor Cyan
    Write-Host ""
    Set-Location $ScriptDir

    $oldPythonUtf8 = $env:PYTHONUTF8
    $oldPythonIoEncoding = $env:PYTHONIOENCODING
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    try {
        $honchoProc = Start-Process -FilePath $pythonExe `
            -ArgumentList "-m", "honcho", "start" `
            -WorkingDirectory $ScriptDir `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $HonchoRawOutLog `
            -RedirectStandardError $HonchoRawErrLog

        $offsetOut = 0
        $offsetErr = 0
        while (-not $honchoProc.HasExited) {
            Flush-HonchoOutput -Path $HonchoRawOutLog -LineOffset ([ref]$offsetOut)
            Flush-HonchoOutput -Path $HonchoRawErrLog -LineOffset ([ref]$offsetErr)
            if ($script:StartupFailed) {
                break
            }
            Start-Sleep -Milliseconds 200
        }
        if ($script:StartupFailed -and -not $honchoProc.HasExited) {
            $null = & cmd.exe /c "taskkill /T /F /PID $($honchoProc.Id) >nul 2>&1"
            $honchoProc.WaitForExit()
            exit 1
        }
        Flush-HonchoOutput -Path $HonchoRawOutLog -LineOffset ([ref]$offsetOut)
        Flush-HonchoOutput -Path $HonchoRawErrLog -LineOffset ([ref]$offsetErr)
    } finally {
        if ($null -eq $oldPythonUtf8) { Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue } else { $env:PYTHONUTF8 = $oldPythonUtf8 }
        if ($null -eq $oldPythonIoEncoding) { Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue } else { $env:PYTHONIOENCODING = $oldPythonIoEncoding }
    }
} catch {
    if ($_.Exception.GetType().Name -eq "PipelineStoppedException" -or $_.Exception.GetType().Name -eq "OperationCanceledException" -or $_.Exception.GetType().Name -eq "HostException") {
        try {
            if ($honchoProc -and -not $honchoProc.HasExited) {
                $null = & cmd.exe /c "taskkill /T /F /PID $($honchoProc.Id) >nul 2>&1"
            }
        } catch { }
        Write-Host "`n[INFO] Interrupted. Exiting..." -ForegroundColor Yellow
        exit 0
    }
    throw
}

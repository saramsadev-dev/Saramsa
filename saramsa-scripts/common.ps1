# Saramsa scripts - shared paths and helpers
# Dot-source from start.ps1, kill.ps1, logs.ps1

$ErrorActionPreference = "Stop"

# Project root = parent of saramsa-scripts
$ScriptDir = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "saramsa-ai"
$CeleryOpsUIDir = Join-Path $ScriptDir "celery_ops" | Join-Path -ChildPath "celery_ops" | Join-Path -ChildPath "ui" | Join-Path -ChildPath "react"
# Canonical PID file path so start/kill use same file
$PidFile = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir ".saramsa-pids.json"))
$FrontendLog = Join-Path $ScriptDir ".saramsa-frontend.log"
$BackendLog = Join-Path $ScriptDir ".saramsa-backend.log"
$BackendErrLog = Join-Path $ScriptDir ".saramsa-backend.err.log"
$CeleryLog = Join-Path $ScriptDir ".saramsa-celery.log"
$CeleryErrLog = Join-Path $ScriptDir ".saramsa-celery.err.log"
$CeleryOpsLog = Join-Path $ScriptDir ".saramsa-celery-ops.log"
$CeleryOpsErrLog = Join-Path $ScriptDir ".saramsa-celery-ops.err.log"

$VenvPath = Join-Path $BackendDir "venv"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
$UseVenv = (Test-Path $VenvActivate)

function Save-ProcessId { param([string]$ServiceName, [int]$ProcessId)
    $Pids = @{}
    if (Test-Path $PidFile) {
        $j = Get-Content $PidFile -Raw | ConvertFrom-Json
        $j.PSObject.Properties | ForEach-Object { $Pids[$_.Name] = $_.Value }
    }
    $Pids[$ServiceName] = $ProcessId
    $Pids | ConvertTo-Json | Out-File -FilePath $PidFile -Encoding UTF8
}

function Load-ProcessIds {
    $Pids = @{}
    if (Test-Path $PidFile) {
        $j = Get-Content $PidFile -Raw | ConvertFrom-Json
        $j.PSObject.Properties | ForEach-Object { $Pids[$_.Name] = $_.Value }
    }
    return $Pids
}

function Clear-ProcessIds {
    try { if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue } } catch { }
}

function Test-PortListening { param([string]$TargetHost = "127.0.0.1", [int]$Port = 3001, [int]$TimeoutMs = 2000)
    $tcp = $null
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $task = $tcp.ConnectAsync($TargetHost, $Port)
        $null = $task.Wait($TimeoutMs)
        if ($task.IsCompleted -and -not $task.IsFaulted -and $tcp.Connected) { return $true }
    } catch { }
    finally { if ($tcp) { try { $tcp.Dispose() } catch {} } }
    return $false
}

function Check-Redis {
    try { if ((redis-cli ping 2>$null) -eq "PONG") { return $true } } catch { }
    $tcp = $null
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $task = $tcp.ConnectAsync("127.0.0.1", 6379)
        $null = $task.Wait(2000)
        if ($task.IsCompleted -and -not $task.IsFaulted -and $tcp.Connected) { return $true }
    } catch { }
    finally { if ($tcp) { try { $tcp.Dispose() } catch {} } }
    return $false
}

function Check-WSL {
    try { if ((wsl --version 2>$null) -or ($LASTEXITCODE -eq 0)) { return $true } } catch { }
    try { wsl --list --quiet 2>$null | Out-Null; if ($LASTEXITCODE -eq 0) { return $true } } catch { }
    return $false
}

function Check-WindowsRedis {
    try { if (Get-Command redis-server -ErrorAction SilentlyContinue) { return $true } } catch { }
    foreach ($p in @("C:\Program Files\Redis\redis-server.exe", "C:\redis\redis-server.exe", "$env:ProgramFiles\Redis\redis-server.exe")) {
        if (Test-Path $p) { return $true }
    }
    return $false
}

function Install-RedisWindows {
    Write-Host ""
    Write-Host "Redis is required but not installed." -ForegroundColor Yellow
    Write-Host "  1. Chocolatey: choco install redis-64 -y" -ForegroundColor Gray
    Write-Host "  2. Manual: https://github.com/tporadowski/redis/releases" -ForegroundColor Gray
    Write-Host ""
    $r = Read-Host "Install Redis via Chocolatey now? (Y/N)"
    if ($r -eq "Y" -or $r -eq "y") {
        try {
            if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            }
            choco install redis-64 -y
            Write-Host "[OK] Redis installed. Restart PowerShell and run saramsa start all dev" -ForegroundColor Green
        } catch { Write-Host "[ERROR] Install failed: $_" -ForegroundColor Red }
    }
}

function Start-Redis {
    Write-Host "Checking Redis..." -ForegroundColor Cyan
    if (Check-Redis) { Write-Host "[OK] Redis is already running" -ForegroundColor Green; return }
    $wsl = Check-WSL
    $win = Check-WindowsRedis
    if ($wsl) {
        try {
            $null = Start-Process wsl -ArgumentList "bash", "-c", "redis-server --daemonize yes" -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
            foreach ($i in 1..6) {
                Start-Sleep -Seconds 2
                if (Check-Redis) { Write-Host "[OK] Redis started (WSL)" -ForegroundColor Green; return }
            }
            $which = (wsl which redis-server 2>&1) -join " "
            if ($which -match "not found|command not found|no redis") {
                Write-Host "[WARNING] Redis not installed in WSL. Install: wsl sudo apt-get update && wsl sudo apt-get install -y redis-server" -ForegroundColor Yellow
                return
            }
        } catch { }
    }
    if ($win) {
        try {
            $exe = (Get-Command redis-server -ErrorAction SilentlyContinue).Source
            if (-not $exe) { foreach ($p in @("C:\Program Files\Redis\redis-server.exe", "C:\redis\redis-server.exe", "$env:ProgramFiles\Redis\redis-server.exe")) { if (Test-Path $p) { $exe = $p; break } } }
            if ($exe) {
                $null = Start-Process -FilePath $exe -ArgumentList "--service-run" -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
                if (-not $?) { $null = Start-Process -FilePath $exe -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue }
                Start-Sleep -Seconds 3
                if (Check-Redis) { Write-Host "[OK] Redis started (Windows)" -ForegroundColor Green; return }
            }
        } catch { }
    }
    if (-not $wsl -and -not $win) { Install-RedisWindows; Write-Host "[ERROR] Redis required. Install and retry." -ForegroundColor Red; exit 1 }
    Write-Host "[WARNING] Redis failed to start. Start manually:" -ForegroundColor Yellow
    if ($wsl) {
        Write-Host "  wsl redis-server --daemonize yes" -ForegroundColor Gray
        Write-Host "  (If not installed: wsl sudo apt-get update && wsl sudo apt-get install -y redis-server)" -ForegroundColor Gray
    } else {
        Write-Host "  Install Redis (e.g. choco install redis-64) then run redis-server" -ForegroundColor Gray
    }
}

function Stop-AllServices {
    Write-Host "`nStopping all Saramsa services..." -ForegroundColor Yellow
    $killed = @{}
    $n = 0
    $Pids = Load-ProcessIds
    foreach ($sn in @("backend", "celery", "celery-ops", "frontend")) {
        if (-not $Pids.ContainsKey($sn)) { continue }
        $pid_ = $Pids[$sn]
        try {
            $p = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
            if ($p) {
                $null = & taskkill /PID $pid_ /T /F 2>$null
                Write-Host "  Stopped $sn (PID: $pid_)" -ForegroundColor Gray
                $killed[$pid_] = $true
                $n++
            }
        } catch { }
    }
    $portPids = @{}
    try {
        $net = netstat -ano 2>$null
        foreach ($port in @(8000, 3001, 9800)) {
            foreach ($line in ($net | Select-String "LISTENING" | Select-String ":$port\b")) {
                $tokens = ($line.ToString().Trim() -split '\s+')
                $last = $tokens[-1]
                if ($last -match '^\d+$') { $portPids[$last] = $port }
            }
        }
        foreach ($kv in $portPids.GetEnumerator()) {
            $portPid = [int]$kv.Key
            if ($killed.ContainsKey($portPid)) { continue }
            try {
                $qp = Get-Process -Id $portPid -ErrorAction SilentlyContinue
                if ($qp) {
                    $null = & taskkill /PID $portPid /T /F 2>$null
                    Write-Host "  Stopped process on port $($kv.Value) (PID: $portPid)" -ForegroundColor Gray
                    $n++
                }
            } catch { }
        }
    } catch { }
    try {
        $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $cmd = $_.CommandLine
            if (-not $cmd) { return $false }
            ($cmd -match "celery" -and $cmd -match "apis" -and $cmd -match "worker") -or
            ($cmd -match "manage\.py" -and $cmd -match "runserver") -or
            ($cmd -match "celery_ops" -and $cmd -match "serve")
        }
        foreach ($proc in $procs) {
            $pid_ = $proc.ProcessId
            if ($killed.ContainsKey($pid_)) { continue }
            try {
                $qp = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
                if ($qp) {
                    $label = "stray"
                    if ($proc.CommandLine -match "celery_ops") { $label = "celery-ops" }
                    elseif ($proc.CommandLine -match "celery.*apis.*worker") { $label = "celery" }
                    elseif ($proc.CommandLine -match "manage\.py.*runserver") { $label = "backend" }
                    $null = & taskkill /PID $pid_ /T /F 2>$null
                    Write-Host "  Stopped $label (PID: $pid_)" -ForegroundColor Gray
                    $n++
                }
            } catch { }
        }
    } catch { }
    try { wsl bash -c "redis-cli shutdown" 2>$null } catch { }
    try { if (Get-Command redis-cli -ErrorAction SilentlyContinue) { & redis-cli shutdown 2>$null } } catch { }
    Clear-ProcessIds
    Write-Host "[OK] Stopped $n service(s)." -ForegroundColor Green
}

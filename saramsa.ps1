# Saramsa - master CLI
# Usage: saramsa start | saramsa kill | saramsa help
# Delegates to saramsa-scripts/start-procfile.ps1, kill.ps1, help.ps1

param(
    [Parameter(Position=0)][string]$Command = "",
    [Parameter(Position=1)][string]$Arg1 = "",
    [Parameter(Position=2)][string]$Arg2 = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptsDir = Join-Path $ScriptDir "saramsa-scripts"

if (-not (Test-Path $ScriptsDir)) {
    Write-Host "[ERROR] saramsa-scripts not found: $ScriptsDir" -ForegroundColor Red
    exit 1
}

$startProcfileScript = Join-Path $ScriptsDir "start-procfile.ps1"
$killScript = Join-Path $ScriptsDir "kill.ps1"
$logScript = Join-Path $ScriptsDir "log.ps1"
$helpScript = Join-Path $ScriptsDir "help.ps1"

switch ($Command.ToLower()) {
    "start" {
        if ($Arg1 -or $Arg2) {
            Write-Host "[ERROR] 'saramsa start' does not take an environment. Use 'saramsa start'." -ForegroundColor Red
            exit 1
        }
        & $startProcfileScript
    }
    "help" {
        & $helpScript
    }
    "kill" {
        if ($Arg1 -or $Arg2) {
            Write-Host "[ERROR] 'saramsa kill' does not take any arguments. Use 'saramsa kill'." -ForegroundColor Red
            exit 1
        }
        & $killScript
    }
    "log" {
        if (-not $Arg1) {
            Write-Host "[ERROR] Missing log target. Use 'saramsa log frontend' or 'saramsa log all'." -ForegroundColor Red
            exit 1
        }
        & $logScript $Arg1 $Arg2
    }
    default {
        if (-not $Command) {
            Write-Host "[ERROR] No command. Use 'saramsa help'." -ForegroundColor Red
            Write-Host ""
            Write-Host "  saramsa start" -ForegroundColor Yellow
            Write-Host "  saramsa kill" -ForegroundColor Yellow
            Write-Host "  saramsa log frontend" -ForegroundColor Yellow
        } else {
            Write-Host "[ERROR] Unknown command: $Command. Use 'saramsa help'." -ForegroundColor Red
        }
        exit 1
    }
}

# Saramsa - master CLI
# Usage: saramsa start all [dev|prod] | saramsa logs [backend|frontend|celery|celery-ops] | saramsa kill | saramsa help
# Delegates to saramsa-scripts/start.ps1, logs.ps1, kill.ps1, help.ps1

param(
    [Parameter(Position=0)][string]$Command = "",
    [Parameter(Position=1)][string]$Arg1 = "",
    [Parameter(Position=2)][string]$Arg2 = "dev"
)

$ErrorActionPreference = "Stop"

# Normalize "start all dev" -> start-all
if ($Command -eq "start" -and $Arg1 -eq "all") {
    $Command = "start-all"
    $Environment = $Arg2
} elseif ($Command -eq "start" -and $Arg1 -ne "") {
    $Command = "start-all"
    $Environment = $Arg1
} else {
    $Environment = if ($Arg1 -ne "" -and $Arg1 -ne "all") { $Arg1 } else { "dev" }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptsDir = Join-Path $ScriptDir "saramsa-scripts"

if (-not (Test-Path $ScriptsDir)) {
    Write-Host "[ERROR] saramsa-scripts not found: $ScriptsDir" -ForegroundColor Red
    exit 1
}

$startScript = Join-Path $ScriptsDir "start.ps1"
$killScript = Join-Path $ScriptsDir "kill.ps1"
$logsScript = Join-Path $ScriptsDir "logs.ps1"
$helpScript = Join-Path $ScriptsDir "help.ps1"

switch ($Command.ToLower()) {
    "start-all" {
        & $startScript -Env $Environment
    }
    "stop-all" { & $killScript }
    "kill"     { & $killScript }
    "stop"     { & $killScript }
    "logs"     { & $logsScript -Service $Arg1 }
    "help"     { & $helpScript }
    default {
        if (-not $Command) {
            Write-Host "[ERROR] No command. Use 'saramsa help'." -ForegroundColor Red
            Write-Host ""
            Write-Host "  saramsa start all dev" -ForegroundColor Yellow
            Write-Host "  saramsa logs [backend|frontend|celery|celery-ops]" -ForegroundColor Gray
        } else {
            Write-Host "[ERROR] Unknown command: $Command. Use 'saramsa help'." -ForegroundColor Red
        }
        exit 1
    }
}

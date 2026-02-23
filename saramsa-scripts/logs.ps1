# Saramsa logs - tail service logs or show log commands
# Invoked by master saramsa.ps1: & logs.ps1 [-Service backend|frontend|celery|celery-ops]

param([string]$Service = "")

. "$PSScriptRoot\common.ps1"

function Show-LogsHelp {
    Write-Host "Logs:" -ForegroundColor Yellow
    Write-Host "   All:         saramsa logs all   # tail all services in one stream" -ForegroundColor White
    Write-Host "   Backend:     Get-Content '$BackendLog','$BackendErrLog' -Wait -Tail 50" -ForegroundColor White
    Write-Host "   Frontend:    Get-Content '$FrontendLog' -Wait -Tail 50" -ForegroundColor White
    Write-Host "   Celery:      Get-Content '$CeleryErrLog' -Wait -Tail 50   # task/app logs; startup: $CeleryLog" -ForegroundColor White
    Write-Host "   Celery Ops:  Get-Content '$CeleryOpsLog','$CeleryOpsErrLog' -Wait -Tail 50   # API + UI" -ForegroundColor White
}

if (-not $Service) { $Service = "" }
$Service = $Service.Trim().ToLower()

$logs = $null
$name = ""
switch ($Service) {
    "all"            { $logs = @($BackendLog, $BackendErrLog, $FrontendLog, $CeleryLog, $CeleryErrLog, $CeleryOpsLog, $CeleryOpsErrLog); $name = "All services" }
    "backend"        { $logs = @($BackendLog, $BackendErrLog);   $name = "Backend" }
    "frontend"       { $logs = @($FrontendLog);                  $name = "Frontend" }
    "celery"         { $logs = @($CeleryErrLog);                 $name = "Celery" }
    "celery-ops"     { $logs = @($CeleryOpsLog, $CeleryOpsErrLog); $name = "Celery Ops (API + UI)" }
    "celeryops"      { $logs = @($CeleryOpsLog, $CeleryOpsErrLog); $name = "Celery Ops (API + UI)" }
    default {
        Show-LogsHelp
        Write-Host ""
        Write-Host "Usage: saramsa logs [all|backend|frontend|celery|celery-ops]" -ForegroundColor Cyan
        Write-Host "   Omit service to show log paths and tail commands." -ForegroundColor Gray
        exit 0
    }
}

$anyExists = $false
foreach ($l in $logs) { if (Test-Path $l) { $anyExists = $true; break } }
if (-not $anyExists) {
    Write-Host "[WARNING] No log found for $name. Start services first: saramsa start all dev" -ForegroundColor Yellow
    exit 1
}

$existing = @($logs | Where-Object { Test-Path $_ })
Write-Host "Tailing $name log(s) (Ctrl+C to stop): $($existing -join ', ')" -ForegroundColor Cyan
if ($Service -eq "celery") {
    Write-Host "  (Task/app logs from stderr. Worker startup: $CeleryLog)" -ForegroundColor Gray
}
if ($Service -eq "all" -and $existing.Count -gt 0) {
    Write-Host "  (Output is interleaved from all .saramsa-*.log files)" -ForegroundColor Gray
}
Write-Host ""
Get-Content -Path $existing -Wait -Tail 50

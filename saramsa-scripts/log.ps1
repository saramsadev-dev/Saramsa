# Saramsa log - show logs for one service (or all)

param(
    [Parameter(Position=0)][string]$Service = "all",
    [Parameter(Position=1)][string]$Mode = ""
)

. "$PSScriptRoot\common.ps1"

$serviceKey = $Service.ToLowerInvariant()
$follow = $Mode -eq "-f" -or $Mode -eq "--follow"

$logMap = @{
    "frontend"   = $FrontendLog
    "backend"    = $BackendLog
    "celery"     = $CeleryLog
    "celery-ops" = $CeleryOpsLog
    "system"     = $SystemLog
    "all"        = $AllLog
}

if (-not $logMap.ContainsKey($serviceKey)) {
    Write-Host "[ERROR] Unknown log target: $Service" -ForegroundColor Red
    Write-Host "Use one of: frontend, backend, celery, celery-ops, system, all" -ForegroundColor Yellow
    exit 1
}

$target = $logMap[$serviceKey]
if (-not (Test-Path $target)) {
    Write-Host "[ERROR] Log file not found yet: $target" -ForegroundColor Red
    Write-Host "Run 'saramsa start' first to generate logs." -ForegroundColor Yellow
    exit 1
}

Write-Host "Reading $serviceKey logs from: $target" -ForegroundColor Cyan
if ($follow) {
    Get-Content -Path $target -Tail 120 -Wait
} else {
    Get-Content -Path $target -Tail 120
}

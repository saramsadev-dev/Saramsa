# Saramsa help - show usage
# Invoked by master saramsa.ps1: & help.ps1

Write-Host ""
Write-Host "Saramsa Service Manager" -ForegroundColor Magenta
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  saramsa start              - Start all services (Procfile + honcho)" -ForegroundColor White
Write-Host "  saramsa kill               - Stop Saramsa services on ports 8000/3001/9800" -ForegroundColor White
Write-Host "  saramsa log <service>      - Show recent logs for one service" -ForegroundColor White
Write-Host "  saramsa help               - Show this help" -ForegroundColor White
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  start   Start all services in the foreground" -ForegroundColor Gray
Write-Host "  kill    Stop Saramsa services already bound to the app ports" -ForegroundColor Gray
Write-Host "  log     Show logs (append -f to follow)" -ForegroundColor Gray
Write-Host ""
Write-Host "Log targets:" -ForegroundColor Yellow
Write-Host "  frontend | backend | celery | celery-ops | system | all" -ForegroundColor White
Write-Host "  Example: saramsa log frontend -f" -ForegroundColor Gray
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  - Redis        localhost:6379" -ForegroundColor White
Write-Host "  - Frontend     http://localhost:3001" -ForegroundColor White
Write-Host "  - Backend      http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - Celery Ops   http://localhost:9800" -ForegroundColor White
Write-Host ""
Write-Host "Note: Procfile mode runs in the foreground; Ctrl+C stops all." -ForegroundColor Cyan
Write-Host ""

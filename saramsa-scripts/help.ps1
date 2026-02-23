# Saramsa help - show usage
# Invoked by master saramsa.ps1: & help.ps1

Write-Host ""
Write-Host "Saramsa Service Manager" -ForegroundColor Magenta
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  saramsa start all [dev|prod]       - Start all services" -ForegroundColor White
Write-Host "  saramsa logs [all|backend|frontend|celery|celery-ops]  - Tail logs (all = overall)" -ForegroundColor White
Write-Host "  saramsa kill                       - Stop all services" -ForegroundColor White
Write-Host "  saramsa stop                       - Stop all services" -ForegroundColor White
Write-Host "  saramsa help                       - Show this help" -ForegroundColor White
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  start   Start all (Redis, Backend, Celery, Celery Ops, Frontend)" -ForegroundColor Gray
Write-Host "  logs    Tail logs; omit service to show paths and Get-Content commands" -ForegroundColor Gray
Write-Host "  kill    Stop all services (alias: stop)" -ForegroundColor Gray
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  - Redis        localhost:6379" -ForegroundColor White
Write-Host "  - Frontend     http://localhost:3001" -ForegroundColor White
Write-Host "  - Backend      http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - Celery Ops   http://localhost:9800" -ForegroundColor White
Write-Host ""
Write-Host "Logs (tail with 'saramsa logs <service>'):" -ForegroundColor Yellow
Write-Host "  saramsa logs all        - Overall: tail all services in one stream" -ForegroundColor White
Write-Host "  saramsa logs backend   - Django / API" -ForegroundColor White
Write-Host "  saramsa logs celery    - Celery worker (feedback tasks)" -ForegroundColor White
Write-Host "  saramsa logs celery-ops - Celery Ops UI API" -ForegroundColor White
Write-Host "  saramsa logs frontend  - Next.js" -ForegroundColor White
Write-Host "  saramsa logs           - Show all log paths and Get-Content commands" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Press Ctrl+C during start to stop all services." -ForegroundColor Cyan
Write-Host ""

# Saramsa kill - stop all services
# Invoked by master saramsa.ps1: & kill.ps1

. "$PSScriptRoot\common.ps1"
Stop-AllServices

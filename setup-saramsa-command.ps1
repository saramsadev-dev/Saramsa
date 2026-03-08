# Setup script to add 'saramsa' command to PowerShell
# Run this once: .\setup-saramsa-command.ps1

$ScriptPath = $PSScriptRoot
$ScriptFile = Join-Path $ScriptPath "saramsa.ps1"

if (-not (Test-Path $ScriptFile)) {
    Write-Host "[ERROR] saramsa.ps1 not found at: $ScriptFile" -ForegroundColor Red
    exit 1
}

$ProfilePath = $PROFILE.CurrentUserAllHosts
$ProfileDir = Split-Path -Parent $ProfilePath

if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

$FunctionCode = @"

# Saramsa Service Manager Function
function saramsa {
    param(
        [Parameter(Position=0)]
        [string]`$Command = "",

        [Parameter(Position=1)]
        [string]`$Arg1 = ""
    )

    `$ScriptPath = '$ScriptPath'
    `$ScriptFile = Join-Path `$ScriptPath "saramsa.ps1"

    if (Test-Path `$ScriptFile) {
        & `$ScriptFile `$Command `$Arg1
    } else {
        Write-Host "[ERROR] saramsa.ps1 not found at: `$ScriptFile" -ForegroundColor Red
    }
}

"@

$ProfileContent = ""
if (Test-Path $ProfilePath) {
    $ProfileContent = Get-Content $ProfilePath -Raw
}

if ($ProfileContent -match "function saramsa") {
    Write-Host "[WARNING] 'saramsa' function already exists in profile." -ForegroundColor Yellow
    Write-Host "   Updating to latest version..." -ForegroundColor Yellow
    $NewContent = $ProfileContent -replace "(?s)# Saramsa Service Manager Function.*?^}", ""
    $NewContent = $NewContent.TrimEnd() + "`n$FunctionCode"
    Set-Content -Path $ProfilePath -Value $NewContent -Encoding UTF8
    Write-Host "[OK] Function updated! Restart PowerShell or run: . `$PROFILE.CurrentUserAllHosts" -ForegroundColor Green
} else {
    Add-Content -Path $ProfilePath -Value "`n$FunctionCode"
    Write-Host "[OK] 'saramsa' function added to PowerShell profile!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Profile location: $ProfilePath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please restart PowerShell or run:" -ForegroundColor Yellow
    Write-Host "   . `$PROFILE.CurrentUserAllHosts" -ForegroundColor White
    Write-Host ""
    Write-Host "Then you can use:" -ForegroundColor Yellow
    Write-Host "   saramsa start" -ForegroundColor White
}

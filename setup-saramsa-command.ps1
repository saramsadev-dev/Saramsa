# Setup script to add 'saramsa' command to PowerShell
# Run this once: .\setup-saramsa-command.ps1

$ScriptPath = $PSScriptRoot
$ScriptFile = Join-Path $ScriptPath "saramsa.ps1"

if (-not (Test-Path $ScriptFile)) {
    Write-Host "[ERROR] saramsa.ps1 not found at: $ScriptFile" -ForegroundColor Red
    exit 1
}

# Get PowerShell profile path
$ProfilePath = $PROFILE.CurrentUserAllHosts
$ProfileDir = Split-Path -Parent $ProfilePath

# Create profile directory if it doesn't exist
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

# Function to add to profile
$FunctionCode = @"

# Saramsa Service Manager Function
function saramsa {
    param(
        [Parameter(Position=0)]
        [string]`$Command = "",
        
        [Parameter(Position=1)]
        [string]`$Arg1 = "",
        
        [Parameter(Position=2)]
        [string]`$Arg2 = ""
    )
    
    `$ScriptPath = '$ScriptPath'
    `$ScriptFile = Join-Path `$ScriptPath "saramsa.ps1"
    
    if (Test-Path `$ScriptFile) {
        & `$ScriptFile `$Command `$Arg1 `$Arg2
    } else {
        Write-Host "[ERROR] saramsa.ps1 not found at: `$ScriptFile" -ForegroundColor Red
    }
}

"@

# Check if function already exists
$ProfileContent = ""
if (Test-Path $ProfilePath) {
    $ProfileContent = Get-Content $ProfilePath -Raw
}

if ($ProfileContent -match "function saramsa") {
    Write-Host "[WARNING] 'saramsa' function already exists in profile." -ForegroundColor Yellow
    Write-Host "   Updating to latest version..." -ForegroundColor Yellow
    # Remove old function and add new one
    $NewContent = $ProfileContent -replace "(?s)# Saramsa Service Manager Function.*?^}", ""
    $NewContent = $NewContent.TrimEnd() + "`n$FunctionCode"
    Set-Content -Path $ProfilePath -Value $NewContent -Encoding UTF8
    Write-Host "[OK] Function updated! Restart PowerShell or run: . `$PROFILE" -ForegroundColor Green
} else {
    # Append function to profile
    Add-Content -Path $ProfilePath -Value "`n$FunctionCode"
    Write-Host "[OK] 'saramsa' function added to PowerShell profile!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Profile location: $ProfilePath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please restart PowerShell or run:" -ForegroundColor Yellow
    Write-Host "   . `$PROFILE" -ForegroundColor White
    Write-Host ""
    Write-Host "Then you can use:" -ForegroundColor Yellow
    Write-Host "   saramsa start all dev" -ForegroundColor White
    Write-Host "   saramsa logs [backend|frontend|celery|celery-ops]" -ForegroundColor White
    Write-Host "   saramsa kill" -ForegroundColor White
}

@echo off
REM Saramsa - One-time PATH setup
REM Run this once (as your normal user) to add 'saramsa' to your PATH.
REM After running, open a NEW terminal and 'saramsa start' will work from anywhere.

setlocal

REM Get the directory where this script lives (the repo root)
set "SARAMSA_DIR=%~dp0"
REM Remove trailing backslash
if "%SARAMSA_DIR:~-1%"=="\" set "SARAMSA_DIR=%SARAMSA_DIR:~0,-1%"

REM Check if already in PATH
echo %PATH% | findstr /I /C:"%SARAMSA_DIR%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] Saramsa is already in your PATH.
    echo      Directory: %SARAMSA_DIR%
    echo      You can run 'saramsa start' from any terminal.
    goto :done
)

REM Add to user PATH (not system PATH - no admin needed)
echo Adding Saramsa to your user PATH...
echo   Directory: %SARAMSA_DIR%

REM Read current user PATH, append our directory
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CURRENT_USER_PATH=%%B"

if defined CURRENT_USER_PATH (
    setx PATH "%CURRENT_USER_PATH%;%SARAMSA_DIR%" >nul 2>&1
) else (
    setx PATH "%SARAMSA_DIR%" >nul 2>&1
)

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Saramsa added to your PATH successfully.
    echo      Open a NEW terminal and run: saramsa start
) else (
    echo.
    echo [ERROR] Failed to update PATH. You can add it manually:
    echo   1. Open Settings ^> System ^> About ^> Advanced system settings
    echo   2. Click "Environment Variables"
    echo   3. Under "User variables", edit "Path"
    echo   4. Add: %SARAMSA_DIR%
)

:done
endlocal
pause

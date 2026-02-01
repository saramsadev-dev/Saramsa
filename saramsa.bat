@echo off
REM Saramsa Service Manager - Batch Wrapper
REM Usage: saramsa start-all dev

powershell.exe -ExecutionPolicy Bypass -File "%~dp0saramsa.ps1" %*
